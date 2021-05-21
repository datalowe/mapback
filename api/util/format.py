def parse_float_round(dec_str, num_dec=4):
    """
    Parses a passed string, rounds the resulting value to a specified (default 4)
    number of decimals, and returns the result.
    """
    float_val = float(dec_str)
    return round(float_val, 4)

def round_coords(coord_tup, num_dec=4):
    """
    Takes in a 2-element tuple of strings holding decimal/float values
    (or simply float values), parses the float values, rounds them to
    the specified number of decimals (defaults to 4) and returns the result.
    """
    first_val = parse_float_round(coord_tup[0], num_dec)
    second_val = parse_float_round(coord_tup[1], num_dec)
    return (first_val, second_val)