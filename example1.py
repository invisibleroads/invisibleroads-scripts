from models import Goal, Note, db


g1 = Goal(id='a', text='goal1')
db.add(g1)
db.commit()

g2 = Goal(id='b', text='goal2')
db.add(g2)
db.commit()

g3 = Goal(id='c', text='goal3', parents=[g1, g2])
db.add(g3)
db.commit()

g4 = Goal(id='d', text='goal4', parents=[g2])
db.add(g4)
db.commit()

n1 = Note(id='1', text='note1', goal_id=g1.id)
db.add(n1)
db.commit()

n2 = Note(id='2', text='note2', goal_id=g3.id)
db.add(n2)
db.commit()

print(n1)
# print(n2)
print(g1.children)
print(g2.children)

print(n1)
