import sys
import numpy as np
from subprocess import Popen

batchSize = 15 

# builtin4 = [5001, 5002, 5003, 5004, 5005, 5006, 5007, 5008, 5009, 5010, 5011, 5012, 5013, 5014, 5015, 5016, 5017, 5018, 5019, 5020, 5021, 5022, 5024, 5025, 5026]
# anchoring4 = [2351480, 2244316, 3315653, 1962547, 2025970, 1437284, 1026355, 3361693, 1618360, 1446417, 2096533, 1698327, 1663325, 3058685, 1879037, 3044920, 1804069, 2417650, 1898895, 1026359, 1026363, 2957509, 3203677, 1875035, 1026367, 1695913, 1637582, 2439395, 1906512, 1026371, 1722410, 3103412, 1765533, 2457234, 2386536, 1842488, 2053744, 1042417, 1664873, 2924502, 1026375, 2055768, 1596619, 1042255, 1999831, 1768115, 3321322, 1861850, 1404703, 1864028, 1835778, 1696927, 1878008, 1583040, 2004731, 1413039, 1929377, 1026379, 1026383, 1907465, 1442070, 1042403, 1639699, 1421786, 2037869, 3062261, 1401947, 1043286, 2395060, 1423186, 3295749, 1577725, 1591156, 1026387, 1849605, 1402339, 1425314, 1791291, 1026391, 2923644, 1404333, 1769991, 1789806, 1790199, 1026395, 2464285, 1664730, 2063464, 3021099, 1402317, 1769335, 1765882, 1042245, 2067456, 1026399, 1790203, 1425318, 1042421, 2016840, 1880334, 2456804, 2398519, 2020876, 3217639, 1026403, 1891018, 1733341, 1962551, 2966283, 2037106, 2020834, 1404595, 1790232, 2841887, 1402084, 1929323, 1668851, 1575997, 1666914, 1835746, 1421259, 1589862, 1748022, 2435592, 1796567, 2904335, 1789561, 1789538, 1026407, 1842448, 1596739, 1845531, 3360589, 1217480, 1217480, 1043457, 1790332, 1698331, 1803655, 1726645, 1790207, 2394115, 1672156, 1039806, 1791209, 1665836, 1675583, 1768005, 2014981, 1042425, 1801217, 2339923, 1666038, 2398550, 2852012, 1566674, 1042407, 1817189, 2017398, 1806570, 1790944, 2339853, 2021326, 1672028, 1726568, 1791306, 2856282, 1990233, 1698335, 1603550, 1612282]
# extraMsm = [1591146]
# allmsm.extend(builtin4)
# allmsm.extend(anchoring4)
# allmsm.extend(extraMsm)
blacklist=[1789781, 1818204, 2024335, 2024378, 2444159, 2444158, 5051, 5151, 1851699, 1766262,2221829] # spraying msm () are too memory consuming for the forwarding anomaly analysis

allmsm =[2067456, 1043457, 2394115, 1801217, 2398550, 1769991, 2435592, 1851699, 
        2020876, 2339853, 1446417, 3622418, 1698327, 5356561, 4480004, 1698331, 
        3678236, 2464285, 5151, 4421111, 2957509, 1875035, 2004731, 1864028, 1722410, 
        6937607, 4448813, 3787311, 1768115, 4439604, 1748022, 1962551, 3044920, 
        2841147, 6886972, 1575997, 3579455, 5332452, 2966283, 6918724, 1768005, 
        2016840, 3917496, 2339923, 6937686, 2055768, 1990233, 1401947, 3203677, 
        4438111, 1789538, 1685091, 1437284, 1817189, 1589862, 2439395, 1726568, 
        1004651, 1004653, 4464317, 2053744, 2063464, 3361639, 2444159, 2017398, 
        1789561, 4442235, 2923644, 4377618, 1929323, 3534345, 4646023, 3917962, 
        5332503, 6938121, 2037869, 2841887, 2457234, 2014981, 3677491, 6721690, 
        1854619, 1765533, 1696927, 1929377, 4587781, 3599015, 3548328, 1695913, 
        3564715, 2852012, 1684936, 1404595, 3103412, 1726645, 5376694, 4582071, 
        3596831, 3558675, 1698335, 1891018, 6892224, 1004741, 2386536, 1596739, 
        1596619, 4418082, 1637582, 1791291, 5460117, 1962547, 4451545, 1664730, 
        2244316, 1733341, 1835746, 1670371, 1402084, 3217639, 1791209, 1806570, 
        3295749, 3606482, 6930167, 1668851, 4426485, 6922486, 1790199, 1004795, 
        1577725, 1790207, 6951296, 1835778, 4580139, 1849605, 3560200, 1907465, 
        1999831, 3558669, 1880334, 2904335, 1842448, 1639699, 1442070, 1790232, 
        3834137, 3834138, 1845531,1861850, 4371230, 1404703, 3577501, 1804069, 
        3789094, 3603761, 3021099, 1665836, 1887537, 1026355, 4704387, 1026359, 
        1842488, 1026363, 3917118, 1026367, 2398519, 1026371, 1042245, 6928465, 
        6115164, 5339183, 1791306, 1026379, 6929228, 3360589, 1042255, 1906512, 
        4104529, 1423186, 1402339, 1789781, 1043286, 1026391, 6931429, 2456804, 
        2856282, 1026395, 1672028, 1663325, 1026399, 1666914, 1026403, 1026407, 
        1664873, 1591146, 1789806, 3624303, 2037106, 1591156,  1769335, 
        2351480, 1860500, 1675583, 1790332, 2096533, 3624320, 2417650, 3361631, 
        1803655, 5001, 6943118, 5004, 5005, 5006, 1898895, 5008, 5009, 5010, 5011, 
        5012, 5013, 5014, 5015, 5016, 5017, 5019, 3361693, 3858501, 3560194, 1425314, 
        5027, 5028, 5029, 5030, 5031, 4492712, 5402540, 1404333, 1413039, 3614641, 
        2395060, 1618360, 1685434, 5051, 1039806, 3062261, 1583040, 3624067, 3315653, 
        1217480, 1421259, 1402317, 2021326, 4622289, 1566674,  2924502, 
        1796567, 1421786, 1026383, 1672156, 1765882, 1603550, 1790944, 2020834, 
        1042403, 2024335, 1425318, 1042407, 3321322, 3058685, 1685486, 1004797, 
        1042417, 2025970, 3484659, 1042421, 1666038, 1790203, 1878008, 1042425, 
        1612282, 1879037] 

allmsm = list(set(allmsm) - set(blacklist))
batches = np.array_split(np.array(allmsm), len(allmsm)/batchSize)

proc = []

if __name__ == "__main__":
    for b in batches:

        args = [str(id) for id in b] 
        cmd = ["python2.7", "stream.py"]
        cmd.extend(args)
        proc.append(Popen(cmd))


    for p in proc:
        p.wait()
