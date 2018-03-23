def slippage(volume, action, book):
    if action == 'sell':
        levels = book['bids']
        price_levels = sorted(levels.keys(), reverse=True)
    elif action == 'buy':
        levels = book['asks']
        price_levels = sorted(levels.keys())
    quote_price = price_levels[0] # either lowest ask or highest bid
    quote_total = volume * quote_price
    actual_total = 0
    volume_to_fill = volume
    for price in price_levels:
        level_volume = levels[price]
        if volume_to_fill - level_volume <= 0:
            actual_total += volume_to_fill * price
            break
        volume_to_fill -= level_volume
        actual_total += level_volume * price
    return actual_total, quote_price, quote_total


if __name__=='__main__':
    book = {'bids': {8962.9: 5.86106893, 8962.2: 0.49877177, 8961: 0.49810183, 8960.1: 0.40911833, 8960: 0.55656053, 8959.8: 0.13452915, 8959.6: 0.1, 8958.4: 0.5001, 8958.3: 0.9174, 8958.1: 1, 8958: 8.29, 8957.8: 0.0050135, 8957.7: 0.49948499, 8957.5: 0.002, 8956.6: 0.1, 8954.8: 0.28966197, 8954.6: 0.5633873, 8954.5: 0.50004267, 8954: 1.499, 8953.8: 0.13452915, 8953.5: 0.49848494, 8953: 8.24, 8951.9: 0.49831686, 8950.4: 2.5, 8950.1: 3}, 'asks': {8963: 1.7092689, 8964: 7.41318758, 8965.6: 0.41137858, 8967: 1.1143, 8967.7: 1.1142, 8967.9: 1.715, 8968: 0.12633553, 8968.9: 1.1137, 8969: 0.025, 8970: 1.25, 8970.1: 0.45, 8973.3: 4.61, 8973.4: 0.45, 8975.4: 0.591, 8976.6: 0.07381446, 8978.5: 0.11288748, 8979: 1.05179565, 8979.1: 0.01327321, 8980: 5.75, 8980.2: 0.02, 8981.6: 0.01179565, 8981.9: 1, 8982: 8, 8982.1: 0.01327321, 8982.4: 0.2}}
    actual_total, quote_price, quote_total = slippage(15, 'sell', book)
    print(actual_total, quote_price, quote_total)