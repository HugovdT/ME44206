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
nidist = (10, 8, 0)
holdingcosts = {"18/10":20, "18/8":10, "18/0":5}

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
J = range(len(nidists))                     # set of steel types
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
     con1[i] = model.addConstr(x[i] <= u_i[i], 'con1[' + str(i) + ']-')

# Constraint 2: demand satisfaction

con2 = {}
for j in J:
    for t in T:
        con2[j,t] = model.addConstr(p[j,t] + (s[j,t-1] for t in ) >= d_jt[j,t] + s[j,t], 'con2[' + str(j) + ',' + str(t) + ']-')

