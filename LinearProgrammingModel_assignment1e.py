from gurobipy import *
import pandas as pd

model = Model ('StainlessSteelProduction')

# ---- Parameters ----
copperLimit = 0.00 # max percentage of copper in the steel

for test in range(0, 30):
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
    cusup_i = copper
    crdem_j = chdist
    nidem_j = nidist
    ef_t = electrolysisFixedCost
    ev_t = electrolysisVariableCost

    # ---- Decission variables ----

    x = {} 
    for i in I:
        for t in T:
            x[i,t] = model.addVar(lb = 0, vtype = GRB.CONTINUOUS, obj = c_i[i], name = 'x[' + str(i) + ',' + str(t) + ']')

    s = {}
    for j in J:
        for t in T:
            s[j,t] = model.addVar(lb = 0, vtype = GRB.CONTINUOUS, obj = h_j[j], name = 's[' + str(j) + ',' + str(t) + ']')

    p = {}
    for j in J:
        for t in T:
            p[j,t] = model.addVar(lb = 0, vtype = GRB.CONTINUOUS, obj = 0, name = 'p[' + str(j) + ',' + str(t) + ']')

    e = {} # define dictionary with electrolysis per month  costs
    for t in T:
        e[t] = LinExpr()
        for i in I:
            e[t] = ef_t + ev_t * x[i,t] * cusup_i[i] 

    b = {}
    for t in T:
        b[t] = model.addVar(lb = 0, vtype = GRB.BINARY, obj = 0, name = 'b[' + str(t) + ']') 


    cost_holding = quicksum(holdingcosts[j] * s[j,t] for j in J for t in T)
    cost_supplier = quicksum(cost[i] * x[i,t] for i in I for t in T)
    cost_electrolysis = quicksum(e[t] * b[t] for t in T)

    costs = cost_holding + cost_supplier + cost_electrolysis

    model.update()
    model.setObjective(costs, GRB.MINIMIZE)
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
                con2[j,t] = model.addConstr(p[j,t] == (d_jt.iloc[j,t] + s[j,t]), 'con2[' + str(j) + ',' + str(t) + ']-')
            else:
                con2[j,t] = model.addConstr((p[j,t] + s[j,t-1]) == (d_jt.iloc[j,t] + s[j,t]), 'con2[' + str(j) + ',' + str(t) + ']-')

    # Constraint 3: max monthly production
    con3 = {}
    for t in T:
        con3[t] = model.addConstr(quicksum(p[j,t] for j in J) <= 100, 'con3[' + str(t) + ']-')

    # Constraint 4: nickel distribution
    con4 = {}
    for t in T:
        con4[t] = model.addConstr(quicksum(nidem_j[j] * p[j, t] for j in J) == quicksum(nisup_i[i] * x[i, t] for i in I), 'con4[' + str(t) + ']-')

    # Constraint 5: chromium distribution
    con5 = {}
    for t in T:
        con5[t] = model.addConstr(quicksum(crdem_j[j] * p[j, t] for j in J)== quicksum(crsup_i[i] * x[i, t] for i in I), 'con5[' + str(t) + ']-')

    # Constraint 6: supply = production
    con6 = {}
    for t in T:
        con6[t] = model.addConstr(quicksum(x[i,t] for i in I) == quicksum(p[j,t] for j in J), 'con6[' + str(t) + ']-')

    # Constraint 7: copper removed from steel
    con7 = {}
    for t in T:
        con7[t] = model.addConstr(quicksum(x[i,t] for i in I) == quicksum(p[j,t] + cusup_i[i] * x[i,t] for i in I for j in J), 'con7[' + str(t) + ']-')

    # Constraint 9: copper under limit
    con8 = {}
    copperTotal = {}
    for t in T:
        copperTotal[t] = quicksum(x[i,t] * cusup_i[i] for i in I)
        con8[t] = model.addConstr(copperTotal[t] <= (copperLimit * quicksum(p[j,t] for j in J)), 'con8[' + str(t) + ']-')

    # Constraint 8: 
    #con9 = {}
    #for j in J:
    #    for t in T:
    #        con9[j,t] = model.addConstr(c[j,t] <= 1000000 * b[j,t], 'con9[' + str(j) + ',' + str(t) + ']-')

    # ---- Solve ----

    model.setParam('OutputFlag', False)  # silencing gurobi output or not
    model.setParam ('MIPGap', 0);       # find the optimal solution
    model.write("output.lp")            # print the model in .lp format file

    model.optimize ()

    # --- Print results ---
    print ('\n----------------------------------------------------------\n')
    print(f"copper limit: ", copperLimit)
    print()
    if model.status == GRB.Status.OPTIMAL: # If optimal solution is found
        print ('All decision variables:\n')
        #for v in model.getVars():
            #if v.x > 0:
                #print('%s: %g' % (v.varName, v.x))
        #x_matrix = pd.DataFrame([[x[i, t].x for t in T] for i in I], index=suppliername, columns=months)
        #s_matrix = pd.DataFrame([[s[j, t].x for t in T] for j in J], index=[f'Steel_{j}' for j in J], columns=months)
        #p_matrix = pd.DataFrame([[p[j, t].x for t in T] for j in J], index=[f'Steel_{j}' for j in J], columns=months)

        #print("\nX matrix (Alloy supply):")
        #print(x_matrix)
        #print("\nS matrix (Storage):")
        #print(s_matrix)
        #print("\nP matrix (Production):")
        #print(p_matrix)

        print ('Total cost : %10.2f euro' % model.objVal)
        print ('')

    else:
        
        print ('\nNo feasible solution found')

    print ('\nREADY\n')

    copperLimit += 0.01
