from gurobipy import *
import pandas as pd
pd.set_option('display.float_format', '{:.2f}'.format)
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
pmax = 100

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

# ---- Decission variables ----

x = {} 
for i in I:
    for j in J:
        for t in T:
            x[i,j,t] = model.addVar(lb = 0, vtype = GRB.CONTINUOUS, obj = c_i[i], name = 'X[' + str(i) + ',' + str(j) + ',' + str(t) + ']')

s = {}
for j in J:
    for t in T:
        s[j,t] = model.addVar(lb = 0, vtype = GRB.CONTINUOUS, obj = h_j[j], name = 'S[' + str(j) + ',' + str(t) + ']')

p = {}
for j in J:
    for t in T:
        p[j,t] = model.addVar(lb = 0, vtype = GRB.CONTINUOUS, obj = 0, name = 'P[' + str(j) + ',' + str(t) + ']')

model.update()
model.modelSense = GRB.MINIMIZE
model.update()
 
# ---- Constraints ----

# Constraint 1: alloy supply
con1 = {}
for i in I:
    for t in T:
        con1[i] = model.addConstr(quicksum(x[i,j,t] for j in J) <= u_i[i], 'con1[' + str(i) + ']-')

# Constraint 2: demand satisfaction

con2 = {}
for j in J:
    for t in T:
        if t == 0:
            con2[j,t] = model.addConstr(p[j,t] == (d_jt.iloc[j,t] + s[j,t]), 'con2[' + str(j) + ',' + str(t) + ']-')
        else:
            con2[j,t] = model.addConstr((p[j,t] + s[j,t-1]) == (d_jt.iloc[j,t] + s[j,t]), 'con2[' + str(j) + ',' + str(t) + ']-')

# Constraint 3: max monthly production
con3 = {}
for t in T:
    con3[t] = model.addConstr(quicksum(p[j,t] for j in J) <= pmax, 'con3[' + str(t) + ']-')

# Constraint 4: nickel distribution
con4 = {}
for t in T:
    for j in J:
        con4[t] = model.addConstr(nidem_j[j] * p[j, t] == quicksum(nisup_i[i] * x[i,j,t] for i in I), 'con4[' + str(t) + ']-')

# Constraint 5: chromium distribution
con5 = {}
for t in T:
    for j in J:
        con5[t] = model.addConstr(crdem_j[j] * p[j, t] == quicksum(crsup_i[i] * x[i,j,t] for i in I), 'con5[' + str(t) + ']-')

# Constraint 6: supply = production
con6 = {}
for t in T:
    for j in J:
        con6[t] = model.addConstr(quicksum(x[i,j,t] for i in I) == p[j, t], 'con6[' + str(t) + ']-')

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
    for i in I:
        for t in T:
            x[i,t] = quicksum(x[i,j,t].x for j in J)

    
    x_matrix = pd.DataFrame(
    [[round(sum(x[i, j, t].x for j in J), 2)  for t in T]for i in I],
    index=suppliername,
    columns=months,
    )
    s_matrix = pd.DataFrame([[s[j, t].x for t in T] for j in J], index=[f'Steel_{j}' for j in J], 
    columns=months
    )
    p_matrix = pd.DataFrame([[p[j, t].x for t in T] for j in J], index=[f'Steel_{j}' for j in J], 
    columns=months
    )

    pd.set_option('display.precision', 2)
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

