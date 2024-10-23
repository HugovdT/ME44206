from gurobipy import *
import pandas as pd

model = Model ('StainlessSteelProduction')

# ---- Parameters ----


# Cargo characteristics
suppliername  = ('sup_a', 'sup_b', 'sup_c', 'sup_d', 'sup_e')
chromium = (0.18, 0.25, 0.15, 0.14, 0) #% chromium    
nickel = (0, 0.15, 0.10, 0.16, 0.10) #% nickel
copper = (0, 0.04, 0.02, 0.05, 0.03) #% copper
maxpermonth = (90, 30, 50, 70, 20) #maximum amount of ore that can be supplied per month
cost = (5, 10, 9, 7, 8.5) #cost per kg of ore
nidist = (0.10, 0.08, 0)
chdist = (0.18, 0.18, 0.18)
holdingcosts = (20, 10, 5)
electrolysisFixedCost = 100 # fixed cost of electrolysis per month (if applied)
electrolysisVariableCost = 5 # variable cost of electrolysis per kg of copper in produced steel (if applied)

# Monthly demand where 18/10, 18/8 and 18/0 are the distributions of chromium and nickel in the stainless steel by percentage
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
data = [[25, 25, 0, 0, 0, 50, 12, 0, 10, 10, 45, 99], [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10], [5, 20, 80, 25, 50, 125, 150, 80, 40, 35, 3, 100]]

# test 0
# data = [[10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],[10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],[10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]

# test 1
# data = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]

# test 2
# data = [[100, 25, 0, 0, 0, 50, 12, 0, 10, 10, 45, 99], [100, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10], [100, 20, 80, 25, 50, 125, 150, 80, 40, 35, 3, 100]]

# test 3
# data = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 250], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 250], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 250]] 

# test 4
# data = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]

# test 5
# import numpy as np
# data = np.random.randint(0, 50, size=(3, 12)).tolist()

monthly_demand = pd.DataFrame(data)

I = range(len(suppliername))                # set of suppliers
J = range(len(nidist))                      # set of steel types
T = range(len(months))                      # set of months

# ---- Parameters ----

c_i = cost
h_j = holdingcosts
d_jt = monthly_demand
u_i = maxpermonth
crsup_i = chromium
nisup_i = nickel
crdem_j = chdist
nidem_j = nidist
ef_t = electrolysisFixedCost
ev_t = electrolysisVariableCost

# ---- Decission variables ----

sup = {} 
for i in I:
    for t in T:
        sup[i,t] = model.addVar(lb = 0, vtype = GRB.CONTINUOUS, obj = c_i[i], name = 'sup[' + str(i) + ',' + str(t) + ']')

sto = {}
for j in J:
    for t in T:
        sto[j,t] = model.addVar(lb = 0, vtype = GRB.CONTINUOUS, obj = h_j[j], name = 'sto[' + str(j) + ',' + str(t) + ']')

prd = {}
for j in J:
    for t in T:
        prd[j,t] = model.addVar(lb = 0, vtype = GRB.CONTINUOUS, obj = 0, name = 'prd[' + str(j) + ',' + str(t) + ']')

cop = {}
for j in J:
    for t in T:
        cop[j,t] = model.addVar(vtype = GRB.CONTINUOUS, obj = 0, name = 'cop[' + str(j) + ',' + str(t) + ']')

#elc = {} # binary variable to decide if electrolysis is applied or not
#for t in T:
#    elc = model.addVar(vtype = GRB.BINARY, obj = ef_t + ev_t * quicksum(cop[j ,t] for j in J), name = 'elc[' + str(t) + ']')

model.update()
model.modelSense = GRB.MINIMIZE
model.update()
 
# ---- Constraints ----

# Constraint 1: alloy supply
con1 = {}
for i in I:
    for t in T:
        con1[i] = model.addConstr(sup[i, t] <= u_i[i], 'con1[' + str(i) + ']-')

# Constraint 2: demand satisfaction

con2 = {}
for j in J:
    for t in T:
        if t == 0:
            con2[j,t] = model.addConstr(prd[j,t] == (d_jt.iloc[j,t] + sto[j,t]), 'con2[' + str(j) + ',' + str(t) + ']-')
        else:
            con2[j,t] = model.addConstr((prd[j,t] + sto[j,t-1]) == (d_jt.iloc[j,t] + sto[j,t]), 'con2[' + str(j) + ',' + str(t) + ']-')

# Constraint 3: max monthly production
con3 = {}
for t in T:
    con3[t] = model.addConstr(quicksum(prd[j,t] for j in J) <= 100, 'con3[' + str(t) + ']-')

# Constraint 4: nickel distribution
con4 = {}
for t in T:
    con4[t] = model.addConstr(quicksum(nidem_j[j] * prd[j, t] for j in J) == quicksum(nisup_i[i] * sup[i, t] for i in I), 'con4[' + str(t) + ']-')

# Constraint 5: chromium distribution
con5 = {}
for t in T:
    con5[t] = model.addConstr(quicksum(crdem_j[j] * prd[j, t] for j in J)== quicksum(crsup_i[i] * sup[i, t] for i in I), 'con5[' + str(t) + ']-')

# Constraint 6: supply = production
con6 = {}
for t in T:
    con6[t] = model.addConstr(quicksum(sup[i, t] for i in I) == quicksum(prd[j, t] for j in J), 'con6[' + str(t) + ']-')

# Constraint 7: copper percentage in produced steel
con7 = {}
for j in J:
    for t in T:
        con7[j,t] = model.addConstr(cop[j,t] == quicksum(copper[i] * sup[i,t] for i in I), 'con7[' + str(j) + ',' + str(t) + ']-')

# ---- Solve ----

model.setParam('OutputFlag', True) # silencing gurobi output or not
model.setParam ('MIPGap', 0);       # find the optimal solution
model.write("output.lp")            # print the model in .lp format file

model.optimize ()


# --- Print results ---
print ('\n--------------------------------------------------------------------\n')
    
if model.status == GRB.Status.OPTIMAL: # If optimal solution is found
    print ('All decision variables:\n')
    for v in model.getVars():
        if v.x > 0:
            print('%s: %g' % (v.varName, v.x))
    x_matrix = pd.DataFrame([[sup[i, t].x for t in T] for i in I], index=suppliername, columns=months)
    s_matrix = pd.DataFrame([[sto[j, t].x for t in T] for j in J], index=[f'Steel_{j}' for j in J], columns=months)
    p_matrix = pd.DataFrame([[prd[j, t].x for t in T] for j in J], index=[f'Steel_{j}' for j in J], columns=months)

    print("\nX matrix (Alloy supply):")
    print(x_matrix)
    print("\nS matrix (Storage):")
    print(s_matrix)
    print("\nP matrix (Production):")
    print(p_matrix)

    print ('Total cost : %10.2f euro' % model.objVal)
    print ('')
    

else:
    print ('\nNo feasible solution found')

print ('\nREADY\n')

