# Quantitative Methods for Logistics Assignment 1
# Gurobi Optimization
#
# Author: Jochem den Nijs
# Version 0.1
# 2024-10-04

from gurobipy import *
import pandas as pd
import numpy as np

model = Model('AlloyCombination')

# ---- Data ----

Steeltype     = ('A', 'B', 'C', 'D', 'E')           # Names of suppliers
SupCrPer = (0.18,  0.25,  0.15,  0.14, 0)        # percentage # Cr_i
SupNiPer = (0,  0.15,  0.10,  0.16, 0.10)        # percentage # Ni_i
SupCuPer = (0,  0.04,  0.02,  0.05, 0.03)        # percentage # Cu_i
MaxSup = (90, 30, 50, 70, 20)                     # kg supply max per supplier #max_i
CostSup = (5, 10, 9, 7, 8.5)                      # ekkies / kg # c_i
Demand1810 = [25, 25, 0, 0, 0, 50, 12, 0, 10, 10, 45, 99] #kg per month # used for d_ik
Demand1808 = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10] #kg per month # used for d_ik
Demand1800 = [5, 20, 80, 25, 50, 125, 150, 80, 40, 35, 3, 100] #kg per month # used for d_ik
DemandName = ("1810", "1808", "1800")
HoldingCosts = (20, 10, 5) #euro's #h_j
PerNiNec = (0.10, 0.08, 0) # percentage of #pNi_j
PerCrNec = 0.18 # percentage of chromiumn needed in all versions #pCr
maxProd = 100 #kg per month #p_max
################# New for E
CuLim = 0.02 # percentage of copper # Cu_max
EC = 100 # euros costs for use of electrolysis
ECkg = 5 # euros per kilo copper

M = 1e6 * 1e6 # Big M-constant

Demand = (Demand1810, Demand1808, Demand1800)
Demand = pd.DataFrame(Demand) # make array for d_ik

# ---- Sets ----

I = range(len(Steeltype))                # set of suppliers
K = range(len(Demand1810))                 # set of months
J = range(len(HoldingCosts))             # set of types of produced steel

# ---- Variables ----

# Decision Variable x(i,k) (bought per supplier)
x = {} 
for i in I:
    for k in K:
        x[i,k] = model.addVar(lb = 0, vtype = GRB.CONTINUOUS, obj = CostSup[i], name = 'X[' + str(i) + ',' + str(k) + ']')

# Decision variable y(j,k) (produced good j per month k)
y = {}
for j in J:
    for k in K:
        y[j,k] = model.addVar(lb = 0, vtype = GRB.CONTINUOUS, obj = 0, name = 'Y[' + str(j) + ',' + str(k) +']')

# Decision variable z(j,k) (storage of type of steel j in month k)
z = {}
for j in J:
    for k in K:
        z[j,k] = model.addVar(lb = 0, vtype = GRB.CONTINUOUS, obj = HoldingCosts[j], name = 'Z[' + str(j) + ',' + str(k) +']')

ECk = {} # define dictionary with electrolysis per month  costs
for k in K:
    ECk[k] = LinExpr()
    ECk[k] = EC + ECkg * quicksum(x[i,k] * SupCuPer[i] for i in I) # add costs per kilo for every month

# Binary Decision variable e(k) to use electrolysis in a month
e = {}
for k in K:
    e[k] = model.addVar(lb = 0, vtype = GRB.BINARY, obj = 0, name = 'E[' + str(k) +']') 

model.update()

# ---- Objective Function ----

CostHolding = quicksum(HoldingCosts[j] * z[j,k] for j in J for k in K)
CostBuying = quicksum(CostSup[i] * x[i,k] for i in I for k in K)
CostElec = quicksum(ECk[k] * e[k] for k in K)

costs = CostHolding + CostBuying + CostElec # define the total costs in an alternative

#model.modelSense = GRB.MINIMIZE
model.setObjective(costs, GRB.MINIMIZE) # Note: this way of handeling it has been changed!
model.update()

# ---- Constraints ----

# Constraints 1: supplier capacity per I
con1 = {}
for i in I:
    for k in K:
        con1[i] = model.addConstr(x[i,k] <= MaxSup[i], 'con1[' + str(i) + ']-')

# Constraints 2: total production capacity
con2 = {}
for k in K:
     con2[k] = model.addConstr(quicksum(y[j,k] for j in J) <= maxProd, 'con2[' + str(k) + ']-')

# Constraints 3: satisfy demand
con3 = {}
for j in J:
    for k in K:
        if k == 0:
            con3[j,k] = model.addConstr((y[j,k] - z[j,k]) == Demand.iloc[j,k], 'con3[' + str(j) + ',' + str(k) + ']-')
        else:
            con3[j,k] = model.addConstr((y[j,k] + z[j,k-1] - z[j,k]) == (Demand.iloc[j,k]), 'con3[' + str(j) + ',' + str(k) + ']-')

# Constraint 4: do not buy more than you produce # Corrected for use of electrolysis
con4 = {}
TotalCuPer = {}
for k in K:
    TotalCuPer[k] = quicksum(x[i,k] * SupCuPer[i] for i in I)
    con4[k] = model.addConstr(quicksum(x[i,k] for i in I) == quicksum(y[j,k] for j in J) - TotalCuPer[k] * e[k], 'con4[' + str(k) + ']-')

# Constraint 5: perfect use of all Ni%
con5 = {}
for k in K:
    con5[k] = model.addConstr(quicksum(SupNiPer[i] * x[i,k] for i in I) == quicksum(PerNiNec[j] * y[j,k] for j in J), 'con5[' + str(k) + ']-')

# Constraint 6: perfect use of all Cr%
con6 = {}
for k in K:
    con6[k] = model.addConstr(quicksum(SupCrPer[i] * x[i,k] for i in I) == quicksum(PerCrNec * y[j,k] for j in J), 'con6[' + str(k) + ']-')

# Constraint 7 & 8: do not go over copper limit or use electrolysis to remove percentage of copper
con7 = {}
#con8 = {}
#con9 = {}
TotalCuPer = {}
for k in K:
    TotalCuPer[k] = quicksum(x[i,k] * SupCuPer[i] for i in I)
    # do not go over copper limit
    con7[k] = model.addConstr(TotalCuPer[k] <= (CuLim * quicksum(y[j,k] for j in J)) + M * e[k], 'con7_no_elec[' + str(k) + ']-') # 1 multiplied with M which makes system suck
    # or removed copper weight is removed -> moved to constraint 4
#    con8[k] = model.addConstr(quicksum(x[i,k] for i in I) - quicksum(y[j,k] for j in J) + TotalCuPer[k] <= M * (1 - e[k]), 'con8_elec[' + str(k) + ']-') # This one could have been added to the general weight constraint which would have been more optimal
#    con9[k] = model.addConstr(quicksum(x[i,k] for i in I) - quicksum(y[j,k] for j in J) + TotalCuPer[k] >= 0, 'con9[' + str(k) + ']-') # make sure statement above does not become negative

model.update()

# ---- Solve ----

model.setParam('OutputFlag', True) # silencing gurobi output or not
model.setParam ('MIPGap', 0);       # find the optimal solution
model.write("output.lp")            # print the model in .lp format file

model.optimize()

# --- Print results ---
print ('\n--------------------------------------------------------------------\n')
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"] 

if model.status == GRB.Status.OPTIMAL: # If optimal solution is found
    print ('Total costs : %10.2f euro' % model.objVal)
    print ('')
    print ('All decision variables:\n')

    print("Produced materials")

    s = '%8s' % ''
    for k in K:
        s = s + '%8s' % months[k]
    print(s)    

    for j in J:
        s = '%8s' % DemandName[j]
        for k in K:
            s = s + '%8.3f' % y[j,k].x
        s = s + '%8.3f' % sum(y[j,k].x for k in K)    
        print (s)    

    s = '%8s' % ''
    for k in K:
        s = s + '%8.3f' % sum(y[j,k].x for j in J)    
    print (s)  

    print("Bought materials")

    s = '%8s' % ''
    for k in K:
        s = s + '%8s' % months[k]
    print(s)    

    for i in I:
        s = '%8s' % Steeltype[i]
        for k in K:
            s = s + '%8.3f' % x[i,k].x
        s = s + '%8.3f' % sum(x[i,k].x for k in K)    
        print(s)    

    s = '%8s' % ''
    for k in K:
        s = s + '%8.3f' % sum(x[i,k].x for i in I)    
    print(s)    

    print("Storage ")

    s = '%8s' % ''
    for k in K:
        s = s + '%8s' % months[k]
    print (s) 

    for j in J:
        s = '%8s' % DemandName[j]
        for k in K:
            s = s + '%8.3f' % z[j,k].x
        s = s + '%8.3f' % sum(z[j,k].x for k in K)    
        print (s)    

    s = '%8s' % ''
    for k in K:
        s = s + '%8.3f' % sum(z[j,k].x for j in J)    
    print(s)   

    print("Electrolysis")

    s = '%8s' % ''
    for k in K:
        s = s + '%8s' % months[k]
    print(s) 

    tekst = ["Binary", "Costs"]
    for p in range(2):
        s = '%8s' % tekst[p]
        for k in K:
            if p == 0:
                s = s + '%8.0f' % e[k].x
            else:
                ECk_value = EC + sum(ECkg * x[i,k].x * SupCuPer[i] for i in I)
                s = s + '%8.3f' % ECk_value  # Print the evaluated cost
        print(s) 

else:
    print ('\nNo feasible solution found')

print ('\nREADY\n')
