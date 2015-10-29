import sys
import networkx as nx
from datetime import datetime
from datetime import timedelta
import os
import json
from IPy import IP
import glob
import numpy as np
import bisect
import matplotlib.pylab as plt
from collections import defaultdict

def isPrivateIP(ip):
    return IP(ip).iptype() == "PRIVATE"

def loadData(path):

    g = nx.Graph()
    files = glob.glob(path)

    for fileNb, filename in enumerate(files):
        
        if os.stat(filename).st_size > 8:
            sys.stderr.write("\rLoading data %02.2f%% (%s)" % ((100.0*(1+fileNb))/len(files), filename))
            fi = open(filename)
            data = json.load(fi)
            fi.close()

            for trace in data:
                if trace["type"] != "traceroute":
                    print "Not a traceroute!?"

                if "error" in trace["result"][0] or "err" in trace["result"][0]["result"]:
                    continue

                ipProbe = "probe_%s"  % trace["prb_id"]
                ip1 = None
                ip2 = None
                lastHop = max(trace["result"], key=lambda x:x['hop'])
                prevRtt = None 

                # try:
                    # if not isPrivateIP(trace["src_addr"]): 
                        # ip1 = trace["src_addr"]
                    # elif trace["from"] and not isPrivateIP(trace["from"]) :
                        # ip1 = trace["from"]
                    # else:
                        # print("Warn: probe as no public IP!")
                        # ip1 = "probe_%s"  % trace["prb_id"]

                # except ValueError:
                    # print trace
                for hop in range(lastHop["hop"]+1):
                    nextHop = next((item for item in trace["result"] if item["hop"] == hop), None)
                    if nextHop is None:
                        continue
                        # TODO: clean that workaround results containing no IP, e.g.:
                        # {u'result': [{u'x': u'*'}, {u'x': u'*'}, {u'x': u'*'}], u'hop': 6}, 

                    if "result" in nextHop and "from" in nextHop["result"][0] and not isPrivateIP(nextHop["result"][0]["from"]):

                        try:
                            ip2 = nextHop["result"][0]["from"]
                            rtt = 3000.0
                            for res in nextHop["result"]:
                            # TODO check if the IP is the same for the 3 packets
                                # if "from" in res and ip2 != res["from"]:
                                    # print "different IPs %s, %s" % (ip2, res["from"])

                                if "rtt" in res and res["rtt"] > 0.0:
                                    rtt = min(rtt, res["rtt"])

                            if rtt==3000.0:
                                # All packets are lost?
                                continue
                            assert rtt >= 0.0

                            # probed path
                            if not g.has_edge(ipProbe, ip2):
                                g.add_edge(ipProbe, ip2, samples=[], type="measured")
                            g.edge[ipProbe][ip2]["samples"].append(rtt)


                            # Infered link
                            if not ip1 is None:
                                if not g.has_edge(ip1, ip2):
                                    g.add_edge(ip1, ip2, samples=[], type="infered")
                                g.edge[ip1][ip2]["samples"].append(rtt - prevRtt)


                        except KeyError as e:
                            print e
                            print trace
                            exit
                            continue

                        except AssertionError:
                            print "rtt value = %s" % rtt
                            print trace

                        finally:
                            prevRtt = rtt
                            ip1 = ip2

    sys.stderr.write("\n")
    return g 


def dataModeling(g):
    """ Compute the probability mass functions for each edges of the given graph.
    """
    nbEdge = 0 
    totalEdge = float(len(g.edges()))
    bins = np.logspace(0,4,100)
    pmfs = {} 
    for n0, n1, data in g.edges_iter(data=True):
        nbEdge+=1.0
        sys.stderr.write("\rData modeling %02.2f%%" % (100.0*(nbEdge+1)/totalEdge))
        absValues = np.abs(data["samples"])
        count = float(len(absValues))
        if count:
            pmfs[(n0,n1)] = np.histogram(absValues,bins)[0]/count

    sys.stderr.write("\n")
    nx.set_edge_attributes(g, "pmf", pmfs)


def testOneTrace(g, trace, edgeType=None):

    proba = {}
    bins = np.logspace(0,4,100)

    if trace["type"] != "traceroute":
        print "Not a traceroute!?"

    if "error" in trace["result"][0] or "err" in trace["result"][0]["result"]:
        return proba

    ipProbe = "probe_%s"  % trace["prb_id"]
    ip1 = None
    ip2 = None
    lastHop = max(trace["result"], key=lambda x:x['hop'])
    prevRtt = None 

    for hop in range(lastHop["hop"]+1):
        nextHop = next((item for item in trace["result"] if item["hop"] == hop), None)
        if nextHop is None:
            continue
            # TODO: clean that workaround results containing no IP, e.g.:
            # {u'result': [{u'x': u'*'}, {u'x': u'*'}, {u'x': u'*'}], u'hop': 6}, 

        if "result" in nextHop and "from" in nextHop["result"][0] and not isPrivateIP(nextHop["result"][0]["from"]):

            ip2 = nextHop["result"][0]["from"]
            rtt = 3000.0
            for res in nextHop["result"]:
            # TODO check if the IP is the same for the 3 packets
                # if "from" in res and ip2 != res["from"]:
                    # print "different IPs %s, %s" % (ip2, res["from"])

                if "rtt" in res and res["rtt"] > 0.0:
                    rtt = min(rtt, res["rtt"])

            if rtt==3000.0:
                # All packets are lost?
                continue
            assert rtt >= 0.0

            # probed path
            if g.has_edge(ipProbe, ip2) and (edgeType is None or edgeType == g.edge[ipProbe][ip2]["type"]):
                proba[(ipProbe, ip2)] = g.edge[ipProbe][ip2]["pmf"][bisect.bisect(bins,rtt)]

            # Infered link
            if not ip1 is None:
                if g.has_edge(ip1, ip2):
                    proba[(ip1,ip2)] = g.edge[ip1][ip2]["pmf"][bisect.bisect(bins,rtt - prevRtt)]

    return proba


def testDateRange(g,start = datetime(2015, 5, 12, 23, 45), 
        end = datetime(2015, 5, 13, 23, 45), msmIDs = range(5001,5027), edgeType=None):

    timeWindow = timedelta(minutes=30)
    res = {}

    for i, msmId in enumerate(msmIDs):
        currDate = start
        stats = defaultdict(list)
        sys.stderr.write("\rTesting %02.2f%% (measurement id %s)" % (100.0*(1+i)/len(msmIDs), msmId) )
        while currDate+timeWindow<end:
            totalProb = [] 

            if not os.path.exists("data/%s_msmId%s.json" % (currDate, msmId)):
                currDate += timeWindow
                continue

            fi = open("data/%s_msmId%s.json" % (currDate, msmId) )
            data = json.load(fi)

            for trace in data:
                prob = testOneTrace(g,trace,edgeType)
                totalProb.extend(prob.values())

            if len(totalProb):
                stats["date"].append(currDate)
                stats["mean"].append(np.mean(totalProb))
                stats["median"].append(np.median(totalProb))
                stats["std"].append(np.std(totalProb))

            currDate += timeWindow

        res[msmId] = stats 
    
    sys.stderr.write("\n")
    return res

def plotTestDateRange(res):

    for msmId, (x,y) in res.iteritems():
        plt.plot(x,y,label=msmId)

    plt.grid(True)
    plt.legend()
    plt.savefig("firstTry.eps")
