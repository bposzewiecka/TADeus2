from scipy.stats import geom


def get_eval_pvalue(n, theta = 0.09241035129185671 , p = 0.011742364113774086):

    if n == 0: return 1 - theta 
    
    return  1 - (theta + (1-theta) * geom.cdf(n, p, loc=0))
