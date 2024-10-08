# Airplane cargo example - Hillier and Lieberman ed. 10, problem 3.4-14)
# Gurobi Optimization
#
# Author: Mark Duinkerken
# Version 0.1
# 2017-10-19


from gurobipy import *

model = Model ('AirplaneCargo')


# ---- Parameters ----


# Cargo characteristics
cargoname     = ('bulk_1', 'bulk_2', 'bulk_3', 'bulk_4')
cargoquantity = ( 20,  12,  30,  11)        # ton
cargovolume   = (500, 700, 600, 400)        # m3 / ton
cargoprofit   = (320, 400, 360, 290)        # euro / ton

# Compartment characteristics
compname  = ('front', 'center', 'back')
maxweight = (12, 18, 10)                    # ton
maxvolume = (7000, 9000, 5000)              # m3


# ---- Sets ----

I = range (len (cargoname) )                # set of cargo types
J = range (len (compname) )                 # set of compartments


# ---- Variables ----

# Decision Variable x(i,j) (cargo of type in in compartment j)
x = {} 
for i in I:
    for j in J:
        x[i,j] = model.addVar (lb = 0, vtype = GRB.CONTINUOUS, obj = cargoprofit[i], name = 'X[' + str(i) + ',' + str(j) + ']')

# Integrate new variables
model.update ()


# ---- Objective Function ----

model.modelSense = GRB.MAXIMIZE
model.update ()


# ---- Constraints ----

# Constraints 1: volume capacity
con1 = {}
for j in J:
     con1[j] = model.addConstr( quicksum (cargovolume[i] * x[i,j] for i in I) <= maxvolume[j], 'con1[' + str(j) + ']-')

# Constraints 2: weight capacity
con2 = {}
for j in J:
     con2[j] = model.addConstr( quicksum (x[i,j] for i in I) <= maxweight[j], 'con2[' + str(j) + ']-')

# Constraints 3: available amount 
con3 = {}
for i in I:
     con3[i] = model.addConstr( quicksum (x[i,j] for j in J) <= cargoquantity[i], 'con3[' + str(i) + ']-')


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



