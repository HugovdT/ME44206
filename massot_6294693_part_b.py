#QML individual assignement
# Steel production Optimization part B
# Gurobi Optimization
#
# Author: Juliette MASSOT
# October 2024

from gurobipy import *
import pandas as pd


model = Model("Steel_production_optimisation")

#--- Parameters ---

#Scrap characteristics

supplier = ('A','B','C','D','E')

# Scrap composition from each supplier
scrapcr = (0.18, 0.25, 0.15, 0.14, 0)  # Amount of Chromium in 1kg of scrap
scrapni = (0, 0.15, 0.10, 0.16, 0.10)  # Amount of Nickel in 1kg of scrap

# Supplier cost per kg [€/kg]
cost =(5, 10, 9, 7, 8.5)

# Maximum monthly supply for each supplier [kg]
max = (90, 30, 50, 70, 20)


# Product characteristics

product = ('18/10', '18/8', '18/0')

# Product required composition
prodcr = (0.18, 0.18, 0.18)  # Percentage of chromium required
prodni = (0.10, 0.08, 0)  # Percentage of nickel required

# Holding cost for each product [€/kg]
hold = (20, 10, 5)

# Monthly Demand [kg]
month = ('January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December')

demand = ((25,10,5),
            (25, 10, 20),
            (0, 10, 80),
            (0, 10, 25),
            (0, 10, 50),
            (50, 10, 125),
            (12, 10, 150),
            (0, 10, 80),
            (10, 10, 40),
            (10, 10, 35),
            (45, 10, 3),
            (99, 10, 100))

# ---- Sets ----

I = len(supplier) #set of suppliers
J = len(product)  #set of products
T = len(demand)   #set of month

# ---- Variables ----

# Decision variables

# x[i, t, j] is the amount of scrap purchased from supplier i in month t for product j
x = {}
for i in range(I):
    for t in range(T):
        for j in range(J):
            x[i, t, j] = model.addVar(lb=0, vtype=GRB.CONTINUOUS)


# y[j, t] is the amount of stainless steel product j produced in month t
y = {}
for j in range(J):
    for t in range(T):
        y[j,t] =  model.addVar(lb=0, vtype=GRB.CONTINUOUS)

# inv[j, t] is the inventory of product j at the end of month t
inv = {}
for j in range(J):
    for t in range(T+1):
        inv[j, t] =  model.addVar(lb=0, vtype=GRB.CONTINUOUS)

# Integrate new variables
model.update ()


# Objective function: minimize total cost (purchasing + holding costs)
model.setObjective( ( quicksum (x[i, t, j] * cost[i] for i in range(I) for t in range(T) for j in range(J)) ) + ( quicksum (inv[j, t] * hold[j] for j in range(J) for t in range(1,T + 1)) ), GRB.MINIMIZE)

# ---- Constraints ----

# Constraint 1: Maximum monthly supply
for i in range(I):
    for t in range(T):
        model.addConstr( quicksum (x[i, t, j] for j in range(J)) <= max[i] )

# Constraint 2: Total maximum monthly capacity production
for t in range(T):
    model.addConstr( quicksum (y[j, t] for j in range(J)) <= 100)

# Constraint 3: Required amount of Chromium from scrap material for a specific product
for j in range(J):
    for t in range(T):
        model.addConstr( quicksum (x[i, t, j] * scrapcr[i] for i in range(I)) == prodcr[j] * y[j, t])

# Constraint 4: Required amount of Nickel from scrap material for a specific product
for j in range(J):
    for t in range(T):
        model.addConstr( quicksum (x[i, t, j] * scrapni[i] for i in range(I)) == prodni[j] * y[j, t])

# Constraint 5: Demand and storage balance for each month
for j in range(J):
    for t in range(T):
        model.addConstr(y[j, t] + inv[j, t] == demand[t][j] + inv[j, t + 1])

# Constraint 6: No initial storage
model.addConstrs(inv[j, 0] == 0 for j in range(J))

# Constraint 7: No scrap storage at the end of the month
for j in range(J):
    for t in range(T):
        model.addConstr( quicksum (x[i, t, j] for i in range(I)) == y[j, t])


# ---- Solve ----

model.setParam( 'OutputFlag', True) # silencing gurobi output or not
model.setParam ('MIPGap', 0);       # find the optimal solution
model.write("output.lp")            # print the model in .lp format file

model.optimize ()

# --- Print results ---

print ('\n--------------------------------------------------------------------\n')

if model.status == GRB.Status.OPTIMAL: # If optimal solution is found
    print(f"Total minimized cost: {model.objVal:.2f} €")
    print ('')
    print ('All decision variables:\n')

# 1. Amount of scrap pourchased from each supplier each month
scrap_data = {supplier[i]: [0] * T for i in range(I)}
for i in range(I):
    for t in range(T):
        scrap_total_for_month = 0
        for j in range(J):
            scrap_total_for_month += x[i, t, j].X
        scrap_data[supplier[i]][t] = scrap_total_for_month

df_scrap = pd.DataFrame(scrap_data, index=month)
df_scrap.index.name = 'Month'
df_scrap["Total Scrap (kg)"] = df_scrap.sum(axis=1)

print("\nAmount of scrap pourchased from each supplier (kg) :")
print(df_scrap)

# 2. Amount of different steel produced each month
production_data = {product[j]: [0] * T for j in range(J)}
for j in range(J):
    for t in range(T):
        production_data[product[j]][t] = y[j, t].X

df_production = pd.DataFrame(production_data, index=month)
df_production.index.name = 'Month'

print("\nAmount of different steel produced each month (kg) :")
print(df_production)

# 3. Amount of stored product at the end of the month
inventory_data = {product[j]: [0] * T for j in range(J)}
for j in range(J):
    for t in range(T):
        inventory_data[product[j]][t] = inv[j, t + 1].X

df_inventory = pd.DataFrame(inventory_data, index=month)
df_inventory.index.name = 'Month'

print("\nAmount of stored product at the end of the month (kg) :")
print(df_inventory)

print("\n" + "="*50 + "\n")


