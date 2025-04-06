def get_current_exchange_rates():
    return {
        "DKK": 0.13, 
        "NOK": 0.08, 
        "CHF": 1.06, 
        "EUR": 1.00,
        "GBP": 1.18,
        "USD": 0.91,
        "ISK": 0.0069,
    }


if __name__ == "__main__":
    exchange_rates = get_current_exchange_rates()
    for country, rate in exchange_rates.items():
        print(f"{country}: {rate}")
