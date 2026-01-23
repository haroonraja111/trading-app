# Stock Price Auto-Refresh Architecture

## Overview

This document describes the implementation of automatic stock price refreshing every 30 seconds on three key pages:
- `stock_list.html` - List of all stocks
- `stock_detail.html` - Individual stock details
- `dashboard.html` - Portfolio dashboard

The solution uses AJAX polling with `setInterval` to fetch updated prices from the PSX API without reloading the page.

## Architecture

### Backend (Django)

#### 1. API Endpoint: `refresh_stock_prices_api`

**Location:** `trading_app/App/views.py`

**URL Pattern:** `/api/stocks/refresh/`

**Method:** GET

**Purpose:** Batch refresh stock prices for multiple stocks at once, reducing server load and API calls.

**Parameters:**
- `ids=1,2,3` - Refresh stocks by their database IDs (comma-separated)
- `symbols=GAL,CIT,PSO` - Refresh stocks by their symbols (comma-separated)
- `all=true` - Refresh all stocks (use with caution - can be slow)

**Response Format:**
```json
{
    "success": true,
    "updated": 3,
    "stocks": [
        {
            "id": 1,
            "symbol": "GAL",
            "current_price": 125.50,
            "change": 2.30,
            "change_percent": 1.87,
            "volume": 1500000,
            "high": 126.00,
            "low": 124.00
        },
        ...
    ],
    "errors": [
        {
            "symbol": "INVALID",
            "error": "No data available from API"
        }
    ]
}
```

**Key Features:**
- Batch processing: Updates multiple stocks in a single request
- Database updates: Saves fetched prices to the database for persistence
- Error handling: Returns partial results even if some stocks fail
- Security: Protected with `@login_required` decorator

**Code Example:**
```python
@login_required
def refresh_stock_prices_api(request):
    # Get stock IDs or symbols from query parameters
    stock_ids = request.GET.get("ids", "").strip()
    
    # Fetch stocks from database
    stocks_to_refresh = Stock.objects.filter(pk__in=id_list)
    
    # Fetch and update each stock
    for stock in stocks_to_refresh:
        market_data = fetch_stock_from_psx(stock.symbol)
        if market_data:
            stock.current_price = market_data.get("price")
            stock.change = market_data.get("change")
            # ... update other fields
            stock.save()
    
    return JsonResponse({"success": True, "stocks": updated_stocks})
```

#### 2. URL Configuration

**Location:** `trading_app/App/urls.py`

```python
path("api/stocks/refresh/", refresh_stock_prices_api, name="refresh_stock_prices"),
```

**Note:** The API endpoint is placed before dynamic routes like `stocks/<int:pk>/` to ensure proper URL matching.

### Frontend (JavaScript)

#### 1. Stock List Page (`stock_list.html`)

**Refresh Strategy:**
- Collects all stock IDs from the current page
- Sends a single batch request to `/api/stocks/refresh/?ids=1,2,3`
- Updates only price-related fields in the table

**Key Features:**
- **Selective Updates:** Only updates cells with class `price-field` and matching `data-field` attributes
- **Visual Feedback:** Highlights changed cells with green background for 1 second
- **Performance Optimization:** 
  - Prevents concurrent requests with `isRefreshing` flag
  - Pauses refresh when page is hidden (visibility API)
  - Initial refresh after 5 seconds, then every 30 seconds

**HTML Structure:**
```html
<tr data-stock-id="{{ stock.pk }}" data-stock-symbol="{{ stock.symbol }}">
    <td class="price-field" data-field="current_price">Rs. {{ stock.current_price }}</td>
    <td class="price-field" data-field="change">{{ stock.change }}</td>
    <!-- ... -->
</tr>
```

**JavaScript Flow:**
1. On page load, collect all stock IDs from `data-stock-id` attributes
2. Every 30 seconds, send batch request to API
3. For each updated stock, find the corresponding table row
4. Update price fields with visual feedback
5. Handle errors silently (don't disrupt user experience)

#### 2. Stock Detail Page (`stock_detail.html`)

**Refresh Strategy:**
- Fetches price for a single stock
- Updates price fields in the detail view

**Key Features:**
- Single stock refresh (simpler than batch)
- Updates: `current_price`, `high`, `low`
- Same visual feedback and performance optimizations as stock list

**HTML Structure:**
```html
<div class="stock-detail-container" data-stock-id="{{ object.pk }}">
    <span class="stock-detail-value price-field" data-field="current_price">
        Rs. {{ object.current_price }}
    </span>
    <!-- ... -->
</div>
```

#### 3. Portfolio Dashboard (`dashboard.html`)

**Refresh Strategy:**
- Collects unique stock IDs from all holdings
- Fetches updated prices for all stocks
- Updates individual holding rows
- Recalculates portfolio totals (Current Value, Unrealized P/L, P/L %)

**Key Features:**
- **Portfolio Recalculation:** Automatically recalculates totals after price updates
- **Holding Updates:** Updates current price, current value, unrealized P/L, and P/L % for each holding
- **Summary Card Updates:** Updates dashboard summary cards with new totals
- **Color Coding:** Maintains green/red color coding based on profit/loss

**HTML Structure:**
```html
<!-- Summary Cards -->
<div class="stat-value" id="dashboard-total-value">Rs. {{ total_value }}</div>
<div class="stat-value" id="dashboard-unrealized-pl">Rs. {{ unrealized_pl }}</div>

<!-- Holdings Table -->
<tr data-holding-id="{{ holding.pk }}" 
    data-stock-id="{{ holding.stock.pk }}" 
    data-quantity="{{ holding.quantity }}"
    data-buying-price="{{ holding.buying_price }}">
    <td class="price-field" data-field="current_price">Rs. {{ holding.current_price }}</td>
    <td class="price-field" data-field="current_value">Rs. {{ holding.current_value }}</td>
    <!-- ... -->
</tr>
```

**Calculation Logic:**
```javascript
// For each holding:
currentValue = quantity * currentPrice
unrealizedPl = currentValue - totalCost
plPercent = (unrealizedPl / totalCost) * 100

// Portfolio totals:
totalValue = sum of all currentValues
totalUnrealizedPl = totalValue - totalCost
plPercentage = (totalUnrealizedPl / totalCost) * 100
```

## Performance Considerations

### 1. Batch Processing
- **Benefit:** Reduces API calls by fetching multiple stocks in one request
- **Implementation:** Collect all stock IDs, send single request
- **Example:** 10 stocks = 1 API call instead of 10

### 2. Selective Updates
- **Benefit:** Only updates changed fields, not entire page
- **Implementation:** Uses `data-field` attributes to target specific cells
- **Result:** Minimal DOM manipulation, smooth user experience

### 3. Request Throttling
- **Benefit:** Prevents server overload and API rate limiting
- **Implementation:** 
  - 30-second interval between refreshes
  - `isRefreshing` flag prevents concurrent requests
  - Initial delay of 5 seconds to avoid immediate load

### 4. Visibility API
- **Benefit:** Saves resources when page is not visible
- **Implementation:** Pauses refresh when `document.hidden === true`
- **Result:** No unnecessary API calls when user is on another tab

### 5. Error Handling
- **Strategy:** Silent failures with console logging
- **Rationale:** Don't disrupt user experience with error popups
- **Implementation:** Try-catch blocks with graceful degradation

## Security

1. **Authentication:** All endpoints protected with `@login_required`
2. **Input Validation:** Stock IDs and symbols are validated before processing
3. **Error Messages:** Generic error messages to avoid information leakage
4. **CSRF Protection:** Django's CSRF middleware protects POST requests (GET requests are safe for read-only operations)

## API Integration

The solution uses the existing `fetch_stock_from_psx()` function in `services.py`:

```python
def fetch_stock_from_psx(symbol):
    """
    Fetches live stock data from PSX Terminal API.
    Returns dict with: price, change, change_percent, volume, high, low
    """
    url = f"https://psxterminal.com/api/ticks/REG/{symbol.upper()}"
    # ... makes HTTP request with headers
    return market_data
```

## Testing

### Manual Testing Checklist

1. **Stock List Page:**
   - [ ] Verify prices update every 30 seconds
   - [ ] Check visual feedback (green highlight) on changes
   - [ ] Verify no page reload occurs
   - [ ] Test with multiple stocks on page

2. **Stock Detail Page:**
   - [ ] Verify single stock price updates
   - [ ] Check all price fields (current_price, high, low)
   - [ ] Verify visual feedback works

3. **Portfolio Dashboard:**
   - [ ] Verify individual holding prices update
   - [ ] Check portfolio totals recalculate correctly
   - [ ] Verify summary cards update
   - [ ] Test with multiple holdings

4. **Error Handling:**
   - [ ] Test with invalid stock symbols
   - [ ] Test with network errors
   - [ ] Verify graceful degradation

### Performance Testing

- Monitor API response times
- Check browser console for errors
- Verify no memory leaks (long-running intervals)
- Test with large number of stocks (50+)

## Future Enhancements

1. **WebSocket Support:** Replace polling with WebSocket for real-time updates
2. **Caching:** Implement Redis cache for frequently accessed stocks
3. **Rate Limiting:** Add client-side rate limiting to prevent abuse
4. **User Preferences:** Allow users to configure refresh interval
5. **Background Workers:** Move API calls to Celery tasks for better scalability
6. **Price History:** Store historical prices for charting

## Troubleshooting

### Prices Not Updating

1. **Check Browser Console:** Look for JavaScript errors
2. **Verify API Endpoint:** Test `/api/stocks/refresh/?ids=1` directly
3. **Check Network Tab:** Verify AJAX requests are being sent
4. **Database Check:** Ensure stocks exist and have valid symbols

### Performance Issues

1. **Reduce Refresh Frequency:** Change `30000` to `60000` (60 seconds)
2. **Limit Batch Size:** Process stocks in smaller batches
3. **Add Caching:** Cache API responses for 30 seconds

### API Errors

1. **Check API Status:** Verify PSX API is accessible
2. **Review Error Logs:** Check Django server logs for API errors
3. **Fallback Strategy:** Implement fallback to cached prices

## Code Examples

### Backend: API Endpoint
```python
@login_required
def refresh_stock_prices_api(request):
    stock_ids = request.GET.get("ids", "").strip()
    stocks = Stock.objects.filter(pk__in=id_list)
    
    updated_stocks = []
    for stock in stocks:
        market_data = fetch_stock_from_psx(stock.symbol)
        if market_data:
            stock.current_price = market_data.get("price")
            stock.save()
            updated_stocks.append({
                "id": stock.pk,
                "symbol": stock.symbol,
                "current_price": float(stock.current_price)
            })
    
    return JsonResponse({"success": True, "stocks": updated_stocks})
```

### Frontend: Stock List Refresh
```javascript
function refreshStocksData() {
    const stockIds = Array.from(document.querySelectorAll('tr[data-stock-id]'))
        .map(row => row.getAttribute('data-stock-id'));
    
    fetch(`/api/stocks/refresh/?ids=${stockIds.join(',')}`)
        .then(response => response.json())
        .then(data => {
            data.stocks.forEach(stock => {
                const row = document.querySelector(`tr[data-stock-id="${stock.id}"]`);
                const priceCell = row.querySelector('[data-field="current_price"]');
                priceCell.textContent = `Rs. ${stock.current_price.toFixed(2)}`;
            });
        });
}

setInterval(refreshStocksData, 30000);
```

## Conclusion

This implementation provides a scalable, performant solution for auto-refreshing stock prices. The batch processing approach minimizes server load, while the selective DOM updates ensure a smooth user experience. The solution follows Django best practices and can be easily extended with additional features.