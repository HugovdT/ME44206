# Quantitative Methods for Logistics Assignment 1
# Gurobi Optimization
#
# Author: Jochem den Nijs
# Version 0.1
# 2024-10-04


from gurobipy import *

model = Model ('AlloyCombination')


# ---- Data ----

Steeltype     = ('A', 'B', 'C', 'D', 'E')
SupCrPer = ( 0.18,  0.25,  0.15,  0.14, 0)        # percentage
SupNiPer = ( 0,  0.15,  0.10,  0.16, 0.10)        # percentage
SupCuPer = ( 0,  0.04,  0.02,  0.05, 0.03)        # percentage
MaxSup = (90, 30, 50, 70, 20)                     # kg
CostSup = (5, 10, 9, 7, 8.5)                      # ekkies / kg
Demand1810 = (25, 25, 0, 0, 0, 50, 12, 0, 10, 10, 45, 99) #kg per month
Demand1808 = (10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10) #kg per month
Demand1800 = (5, 20, 80, 25, 50, 125, 150, 80, 40, 35, 3, 100) #kg per month
HoldingCosts = (20, 10, 5) #euro's
maxProd = 100 #kg per month
Demand = [Demand1810, Demand1808, Demand1800]

# ---- Sets ----

I = range(len(Steeltype))                # set of suppliers
K = range(len(SupCrPer))                 # set of months
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
        y[j,k] = model.addVar(lb = 0, vtype = GRB.CONTINUOUS, obj = 0, name = 'Y[' + str(j) + ',' + str(k) +']') # klopt het dat het 0 is als obj?

# Decision variable z(j,k) (storage of type of steel j in month k)
z = {}
for j in J:
    for k in K:
        z[j,k] = model.addVar(lb = 0, vtype = GRB.CONTINUOUS, obj = HoldingCost[j], name = 'Z[' + str(j) + ',' + str(k) +']')

model.update ()


# ---- Objective Function ----

model.modelSense = GRB.MINIMIZE
model.update ()


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
            con3[j,k] = model.addConstr((y[j,k] - z[j,k]) >= Demand.iloc[j,k], 'con3[' + str(j) + ',' + str(k) + ']-')
        else:
            con3[j,k] = model.addConstr((y[j,k] + z[j,k-1] - z[j,k]) >= (Demand.iloc[j,k]), 'con3[' + str(j) + ',' + str(k) + ']-')


# end comparison H
# Constraint 4: weight balance first compartment with other compartments
con4 = {}
for j in range (1, len(J)):
    con4[j] = model.addConstr( quicksum (x[i,0] for i in I) * maxweight[j] == quicksum (x[i,j] for i in I) * maxweight[0], 'con4[' + str(j) + ']-')


# ---- Solve ----

model.setParam( 'OutputFlag', True) # silencing gurobi output or not
model.setParam ('MIPGap', 0);       # find the optimal solution
model.write("output.lp")            # print the model in .lp format file

model.optimize ()


# --- Print results ---
print ('\n--------------------------------------------------------------------\n')
    
if model.status == GRB.Status.OPTIMAL: # If optimal solution is found
    print ('Total profit : %10.2f euro' % model.objVal)
    print ('')
    print ('All decision variables:\n')

    s = '%8s' % ''
    for i in I:
        s = s + '%8s' % cargoname[i]
    print (s)    

    for j in J:
        s = '%8s' % compname[j]
        for i in I:
            s = s + '%8.3f' % x[i,j].x
        s = s + '%8.3f' % sum (x[i,j].x for i in I)    
        print (s)    

    s = '%8s' % ''
    for i in I:
        s = s + '%8.3f' % sum (x[i,j].x for j in J)    
    print (s)    

else:
    print ('\nNo feasible solution found')

print ('\nREADY\n')



