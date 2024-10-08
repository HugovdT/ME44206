from gurobipy import *
import pandas as pd

model = Model ('StainlessSteelProduction')

# ---- Parameters ----


# Cargo characteristics
suppliername     = ('sup_a', 'sup_b', 'sup_c', 'sup_d', 'sup_e')
chromium = ( 18,  25,  15,  14, 0) #% chromium    
nickel = (0, 15, 10, 16, 10) #% nickel
copper = (0, 4, 2, 5, 3) #% copper
iron = (82, 56, 73, 65, 87) #% iron
maxpermonth = (90, 30, 50, 70, 20) #maximum amount of ore that can be supplied per month
cost = (5, 10, 9, 7, 8.5) #cost per kg of ore
nidist = (0.10, 0.8, 0)
holdingcosts = (20, 10, 5)

# Monthly demand where 18/10, 18/8 and 18/0 are the distributions of chromium and nickel in the stainless steel by percentage
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
data = {
    'Month': months,
    '18/10': [25, 25, 0, 0, 0, 50, 12, 0, 10, 10, 45, 99],
    '18/8': [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
    '18/0': [5, 20, 80, 25, 50, 125, 150, 80, 40, 35, 3, 100]
}

monthly_demand = pd.DataFrame(data)

I = range(len(suppliername))                # set of suppliers
J = range(len(nidist))                     # set of steel types
T = range(len(months))                      # set of months

# ---- Parameters ----

c_i = cost
h_j = holdingcosts
d_jt = monthly_demand
u_i = maxpermonth
cr_i = chromium
ni_i = nickel
cu_i = copper

# ---- Variables ----

x = {} 
for i in I:
    for t in T:
        x[i,t] = model.addVar(lb = 0, vtype = GRB.CONTINUOUS, obj = c_i[i], name = 'X[' + str(i) + ',' + str(t) + ']')

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
        con1[i] = model.addConstr(x[i, t] <= u_i[i], 'con1[' + str(i) + ']-')

# Constraint 2: demand satisfaction

con2 = {}
for j in J:
    for t in T:
        if t == 0:
            con2[j,t] = model.addConstr(p[j,t] >= (d_jt.iloc[t, j] + s[j,t]), 'con2[' + str(j) + ',' + str(t) + ']-')
        else:
            con2[j,t] = model.addConstr((p[j,t] + s[j,t-1]) >= (d_jt.iloc[t, j] + s[j,t]), 'con2[' + str(j) + ',' + str(t) + ']-')

# Constraint 3: max monthly production
con3 = {}
for t in T:
    con3[t] = model.addConstr(quicksum(p[j,t] for j in J) <= 100, 'con3[' + str(t) + ']-')

# Constraint 4: nickel distribution
con4 = {}
for t in T:
    for j in J:
        con4[t] = model.addConstr(ni_i[j] * p[j, t] == quicksum(ni_i[i] * x[i, t] for i in I), 'con4[' + str(t) + ']-')

# Constraint 5: chromium distribution
con5 = {}
for t in T:
    for j in J:
        con5[t] = model.addConstr(cr_i[j] * p[j, t] == quicksum(cr_i[i] * x[i, t] for i in I), 'con5[' + str(t) + ']-')

# ---- Solve ----

model.setParam( 'OutputFlag', True) # silencing gurobi output or not
model.setParam ('MIPGap', 0);       # find the optimal solution
model.write("output.lp")            # print the model in .lp format file

model.optimize ()


# --- Print results ---
print ('\n--------------------------------------------------------------------\n')
    
if model.status == GRB.Status.OPTIMAL: # If optimal solution is found
    print ('Total cost : %10.2f euro' % model.objVal)
    print ('')
    print ('All decision variables:\n')

    k = '%8s' % ''
    for i in I:
        k = k + '%8s' % suppliername[i]
    print (s)    

    for i in I:
        s = '%8s' % suppliername[i]
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





