import random

USER_TYPES = ['agent', 'supervisor', 'manager', 'deliver']


class Company:
    def __init__(self, id, name):
        self.id = id
        self.name = name


class User:
    def __init__(self, id, username, company_id, role, manager_id=None):
        self.id = id
        self.username = username
        self.company_id = company_id
        self.role = role
        self.manager_id = manager_id

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.username}', role='{self.role}', co={self.company_id}, mgr={self.manager_id})>"


# Setup data
company_a = Company(1, "Company A")
company_b = Company(2, "Company B")
companies = [company_a, company_b]
users = []


def populate_users(count=10):
    names = ["Alex", "Jordan", "Taylor", "Casey", "Morgan",
             "Riley", "Quinn", "Skyler", "Charlie", "Emerson"]

    for i in range(1, count + 1):
        co = random.choice(companies)
        role = random.choice(USER_TYPES)
        name = f"{random.choice(names)}_{i}"

        # Filter potential managers:
        # Must be in the same company and already created to maintain a clean hierarchy
        potential_managers = [u for u in users if u.company_id == co.id]

        # Logic: Managers/Supervisors are less likely to have managers themselves
        # whereas agents and deliverers usually do.
        mgr_id = None
        if potential_managers:
            if role in ['agent', 'deliver'] or random.random() > 0.7:
                mgr_id = random.choice(potential_managers).id

        new_user = User(
            id=i,
            username=name,
            company_id=co.id,
            role=role,
            manager_id=mgr_id
        )
        users.append(new_user)


# Execute
populate_users()

# Display results
print(f"{'ID':<4} | {'Username':<12} | {'Role':<10} | {'Co ID':<6} | {'Mgr ID'}")
print("-" * 50)
for u in users:
    print(f"{u.id:<4} | {u.username:<12} | {u.role:<10} | {u.company_id:<6} | {u.manager_id}")
