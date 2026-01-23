# -------------------------------------------------------------------------------#
#------------------------ views.py ------------------------------------------------#
# -------------------------------------------------------------------------------#
import decimal
from django.shortcuts import render, redirect, get_object_or_404  # Import shortcut functions for rendering, redirecting and object retrieval
from django.contrib.auth.decorators import login_required  # Decorator to require login on certain views
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger  # Imports for pagination handling

from .models import Stock, Trade  # Import Stock and Trade database models
from .forms import StockForm, TradeForm  # Import ModelForms for stocks and trades

from .services import fetch_stock_from_psx
from django.http import JsonResponse

from django.db.models import F, ExpressionWrapper, DecimalField
from django.db.models.functions import Coalesce
# ------------------------ HOME ------------------------

def home_view(request):
    """
    Render the base template or redirect authenticated users to the stock list.
    """
    if request.user.is_authenticated:   # Check if user is logged in
        return redirect("stock_list")   # Redirect authenticated user to stock list page
    return render(request, "App/base.html")  # Render landing page for unauthenticated users

# ------------------------ STOCKS ------------------------

@login_required  # Auth required
def stock_detail_view(request, pk):
    """
    Shows the details of an individual stock, found by primary key.
    """
    stock = get_object_or_404(Stock, pk=pk)  # Find stock by pk or raise 404
    # FIX: The template expects 'object' but we supplied 'stock'.
    # So, pass as 'object' for compatibility with the template.
    return render(request, "App/stocks/stock_detail.html", {"object": stock})  # Show stock detail template

@login_required  # Require login
def stock_update_view(request, pk):
    """
    Handle updating an existing stock. Only accessible to authenticated users.
    Accepts POST data to update an existing Stock entry.
    """
    stock = get_object_or_404(Stock, pk=pk)  # Find stock by pk or raise 404
    
    if request.method == "POST":
        form = StockForm(request.POST, instance=stock)  # Bind form to POST data with existing stock instance
        if form.is_valid():  # If the form is valid
            form.save()  # Save the updated stock to the database
            return redirect("portfolio_dashboard")  # After saving, redirect to portfolio dashboard
    else:
        form = StockForm(instance=stock)  # For GET: create form with existing stock data
    
    return render(request, "App/stocks/stock_form.html", {"form": form, "stock": stock, "is_update": True})  # If GET or invalid, render form again

@login_required  # Require login
def stock_delete_view(request, pk):
    """
    Handle deletion of an existing stock. Only accessible to authenticated users.
    Shows confirmation page on GET, deletes on POST.
    """
    stock = get_object_or_404(Stock, pk=pk)  # Find stock by pk or raise 404
    
    if request.method == "POST":  # If form submitted (confirmation)
        stock.delete()  # Delete the stock from the database
        return redirect("portfolio_dashboard")  # Redirect to portfolio dashboard after deletion
    return render(request, "App/stocks/stock_confirm_delete.html", {"stock": stock})  # Show confirmation page

@login_required  # User must be logged in to access
def stock_list_view(request):
    """
    Display the list of all stocks with pagination.
    Note: User must be authenticated to access this view.
    """
    stocks_list = Stock.objects.all().order_by('symbol')  # Get all stocks ordered by symbol

    paginator = Paginator(stocks_list, 25)  # Set up paginator (25 stocks per page)
    page = request.GET.get('page')  # Get page number from request querystring
    try:
        stocks = paginator.page(page)  # Try to get stocks for requested page
    except PageNotAnInteger:  # If page isn't an integer, show first page
        stocks = paginator.page(1)
    except EmptyPage:  # If page is out of bounds, show last page
        stocks = paginator.page(paginator.num_pages)

    return render(request, "App/stocks/stock_list.html", {"stocks": stocks})  # Pass the page of stocks to template

# ------------------------ TRADES ------------------------

@login_required  # Only logged in users
def trade_create_view(request):
    """
    Allow the logged-in user to create a new trade using TradeForm for validation.
    Handles form submission via POST, otherwise displays an entry form.
    """
    if request.method == "POST":  # If form submitted
        form = TradeForm(request.POST)  # Bind form to POST data
        if form.is_valid():  # If valid
            trade = form.save(commit=False)  # Create trade object, but don't save yet
            trade.user = request.user  # Assign current user to the trade
            trade.save()  # Save trade (will calculate P/L)
            return redirect("portfolio_dashboard")  # Redirect to portfolio dashboard
    else:
        form = TradeForm()  # For GET: create empty form

    return render(  # Render the trade form template
        request,
        "App/Trades/trade_form.html",
        {"form": form}
    )

@login_required  # Must be logged in
def trade_list_view(request):
    """
    Display a list of trades belonging to the logged-in user with pagination.
    """
    trades_list = Trade.objects.filter(user=request.user).select_related('stock').order_by('-created_at')  # Get user's trades, newest first

    paginator = Paginator(trades_list, 25)  # Paginate 25 trades per page
    page = request.GET.get('page')  # Get page number
    try:
        trades = paginator.page(page)  # Get trades for page #page
    except PageNotAnInteger:  # If page isn't a number, use first page
        trades = paginator.page(1)
    except EmptyPage:  # If page outside range, use last page
        trades = paginator.page(paginator.num_pages)

    return render(request, "App/Trades/trade_list.html", {"trades": trades})  # Render trades list to template

@login_required  # Only logged in users
def trade_update_view(request, pk):
    """
    Allow the logged-in user to update an existing trade using TradeForm for validation.
    Handles form submission via POST, otherwise displays an edit form.
    Only allows users to update their own trades.
    """
    trade = get_object_or_404(Trade, pk=pk, user=request.user)  # Find trade by pk and user, or raise 404
    
    if request.method == "POST":  # If form submitted
        form = TradeForm(request.POST, instance=trade)  # Bind form to POST data with existing trade instance
        if form.is_valid():  # If valid
            updated_trade = form.save(commit=False)  # Create trade object, but don't save yet
            updated_trade.user = request.user  # Ensure user is still assigned
            updated_trade.save()  # Save trade (will calculate P/L)
            return redirect("portfolio_dashboard")  # Redirect to portfolio dashboard
    else:
        form = TradeForm(instance=trade)  # For GET: create form with existing trade data

    return render(  # Render the trade form template
        request,
        "App/Trades/trade_form.html",
        {"form": form, "trade": trade, "is_update": True}
    )

@login_required  # Only logged in users
def trade_delete_view(request, pk):
    """
    Handle deletion of an existing trade. Only accessible to authenticated users.
    Shows confirmation page on GET, deletes on POST.
    Only allows users to delete their own trades.
    """
    trade = get_object_or_404(Trade, pk=pk, user=request.user)  # Find trade by pk and user, or raise 404
    
    if request.method == "POST":  # If form submitted (confirmation)
        trade.delete()  # Delete the trade from the database
        return redirect("portfolio_dashboard")  # Redirect to portfolio dashboard after deletion
    return render(request, "App/Trades/trade_confirm_delete.html", {"trade": trade})  # Show confirmation page

# ------------------------ DASHBOARD ------------------------

@login_required  # Dashboard requires login
def portfolio_dashboard(request):
    """
    Show the user's portfolio summary/dashboard.
    Uses model properties for calculations (DRY principle).
    Only logged-in users can view their portfolio dashboard.
    """
    trades = (
        Trade.objects
        .filter(user=request.user)
        .select_related("stock")
    )


    # ---------- FILTER ----------
    stock_filter = request.GET.get('stock', '').strip()   # Get stock filter from URL params if any
    if stock_filter:  # If filter present
        trades = trades.filter(stock__symbol__iexact=stock_filter)


    # ---------- SORT ----------
    sort_by = request.GET.get('sort', 'symbol')  # Get sort type - default to 'symbol'
    if sort_by == "symbol":
        trades = trades.order_by("stock__symbol")  # Sort by symbol

    elif sort_by == "date":
        trades = trades.order_by("-buy_date")  # Sort by buy date descending

    elif sort_by == 'profit':
        trades = trades.annotate(
            pl = ExpressionWrapper(
                (F("quantity") * Coalesce(F("stock__current_price"), decimal.Decimal(0))) - 
                (F("quantity") * F("buying_price")),
                output_field=DecimalField(max_digits=15, decimal_places=2)
            )
        ).order_by(-"pl")

    elif sort_by == 'loss':
        trades = trades.annotate(
            pl=ExpressionWrapper(
                (F("quantity") * F("stock__current_price")) -
                (F("quantity") * F("buying_price")),
                output_field=DecimalField(max_digits=15, decimal_places=2)
            )
        ).order_by("pl")

    # ---------- TOTALS ----------
    total_cost = sum(
        t.quantity *t.buying_price 
        for t in trades
    )  # Total purchase cost

    total_value = sum(
        t.quantity * t.stock.current_price 
        for t in trades 
        if t.stock.current_price
    )
  

    total_unrealized_pl = total_value - total_cost  # Total profit/loss not yet realized
    pl_percentage = round((total_unrealized_pl / total_cost) * 100, 2) if total_cost else 0  # Profit/loss % for portfolio

    context = {  # Prepare all data for rendering the dashboard template
        "holdings": trades,     # All holdings/trades for the user
        "total_cost": total_cost,      # Total invested
        "total_value": total_value,    # Current portfolio value
        "unrealized_pl": total_unrealized_pl,  # Unrealized profit/loss total
        "pl_percentage": pl_percentage,   # Portfolio PL as percent
        "active_trades": trades.count(),  # Number of active trades/holdings
        "user_name": request.user.username,   # Current username
        "sort_by": sort_by,                  # What are we sorting by
        "stock_filter": stock_filter or "",   # What are we filtering by
    }

    return render(request, "App/portfolio/dashboard.html", context)  # Render dashboard with computed data




@login_required
def stock_create_view(request):
    if request.method == "POST":
        form = StockForm(request.POST)
        if form.is_valid():
            stock = form.save(commit=False)

            market_data = fetch_stock_from_psx(stock.symbol)
            if market_data:
                stock.name = market_data["name"]   # ✅ SAVE FULL NAME
                stock.current_price = market_data["price"]
                stock.change = market_data["change"]
                stock.change_percent = market_data["change_percent"]
                stock.volume = market_data["volume"]
                stock.high = market_data["high"]
                stock.low = market_data["low"]

            stock.save()
            return redirect("portfolio_dashboard")
    else:
        form = StockForm()

    return render(request, "App/stocks/stock_form.html", {"form": form})




@login_required
def fetch_stock_price_ajax(request):
    symbol = request.GET.get("symbol", "").strip().upper()

    if not symbol:
        return JsonResponse({"error": "Symbol is required"}, status=400)

    data = fetch_stock_from_psx(symbol)

    if not data or data.get("price") is None:
        return JsonResponse(
            {"error": f"No data found for symbol {symbol}"},
            status=404
        )

    return JsonResponse({
        "symbol" : data["symbol"],
        "name": data["name"],   # ✅ COMPANY NAME
        "price": float(data["price"]),
        "high": float(data["high"]) if data.get("high") else "",
        "low": float(data["low"]) if data.get("low") else "",
        "volume": int(data["volume"]) if data.get("volume") else "",
    })


@login_required
def refresh_stock_prices_api(request):
    """
    API endpoint to refresh stock prices for multiple stocks at once.
    Accepts stock IDs or symbols via query parameters.
    Returns updated price data for all requested stocks.
    
    Usage:
    - /api/stocks/refresh/?ids=1,2,3 (refresh by stock IDs)
    - /api/stocks/refresh/?symbols=GAL,CIT,PSO (refresh by symbols)
    - /api/stocks/refresh/?all=true (refresh all stocks - use with caution)
    """
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    # Get parameters
    stock_ids = request.GET.get("ids", "").strip()
    symbols = request.GET.get("symbols", "").strip()
    refresh_all = request.GET.get("all", "").lower() == "true"
    
    stocks_to_refresh = []
    
    # Determine which stocks to refresh
    if refresh_all:
        # Refresh all stocks (use with caution - can be slow)
        stocks_to_refresh = Stock.objects.all()
    elif stock_ids:
        # Refresh by IDs
        try:
            id_list = [int(id.strip()) for id in stock_ids.split(",") if id.strip()]
            stocks_to_refresh = Stock.objects.filter(pk__in=id_list)
        except ValueError:
            return JsonResponse({"error": "Invalid stock IDs format"}, status=400)
    elif symbols:
        # Refresh by symbols
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        stocks_to_refresh = Stock.objects.filter(symbol__in=symbol_list)
    else:
        return JsonResponse({"error": "Please provide 'ids', 'symbols', or 'all=true' parameter"}, status=400)
    
    if not stocks_to_refresh.exists():
        return JsonResponse({"error": "No stocks found"}, status=404)
    
    # Fetch and update prices for each stock
    updated_stocks = []
    errors = []
    
    for stock in stocks_to_refresh:
        try:
            # Fetch latest data from API
            market_data = fetch_stock_from_psx(stock.symbol)
            
            if market_data and market_data.get("price") is not None:
                # Update stock in database
                stock.current_price = market_data.get("price")
                stock.change = market_data.get("change")
                stock.change_percent = market_data.get("change_percent")
                stock.volume = market_data.get("volume")
                stock.high = market_data.get("high")
                stock.low = market_data.get("low")
                stock.save()
                
                # Add to response
                updated_stocks.append({
                    "id": stock.pk,
                    "symbol": stock.symbol,
                    "current_price": float(stock.current_price) if stock.current_price else None,
                    "change": float(stock.change) if stock.change else None,
                    "change_percent": float(stock.change_percent) if stock.change_percent else None,
                    "volume": int(stock.volume) if stock.volume else None,
                    "high": float(stock.high) if stock.high else None,
                    "low": float(stock.low) if stock.low else None,
                })
            else:
                errors.append({
                    "symbol": stock.symbol,
                    "error": "No data available from API"
                })
        except Exception as e:
            errors.append({
                "symbol": stock.symbol,
                "error": str(e)
            })
    
    return JsonResponse({
        "success": True,
        "updated": len(updated_stocks),
        "stocks": updated_stocks,
        "errors": errors
    })
