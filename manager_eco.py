# formulas to calculate eco

#parameters
Max_eco_per_tile = 100
eco_growth_rate_per_troop = 0.1
eco_growth_amount_per_tile = 10


def generate_eco_based_on_territories(territories, currenteco):
    max_eco = Max_eco_per_tile * territories
    growth = eco_growth_amount_per_tile * territories
    new_eco = currenteco + growth
    if new_eco > max_eco:
        new_eco = max_eco
    
    return new_eco, growth

def generate_eco_based_on_troops(territories, troops, currenteco):
    max_eco = Max_eco_per_tile * territories
    growth = eco_growth_rate_per_troop * troops
    new_eco = currenteco + growth
    if new_eco > max_eco:
        new_eco = max_eco

    return new_eco, growth
