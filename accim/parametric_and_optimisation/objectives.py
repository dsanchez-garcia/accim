def average_results(result):
    return result.data["Value"].mean()
def sum_results(result):
    return result.data["Value"].sum()
def return_time_series(result):
    return result.data["Value"].to_list()
