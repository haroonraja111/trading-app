# --------------------------------------------------------#
#------------------------ models.py-----------------------#
# --------------------------------------------------------#
from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Stock(models.Model):
    symbol = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)

    # Current Prices
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    change = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    change_percent = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)

    # Take Profits
    tp1 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tp2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tp3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Stop Losses
    sl1 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sl2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sl3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Indicators
    rsi = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Last Traded Prices
    ltp1 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ltp2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ltp3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Price Range
    low = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    high = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.symbol


class Trade(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField()
    buying_price = models.DecimalField(max_digits=10, decimal_places=2)
    buy_date = models.DateField()

    # Targets
    mtp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    msl = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Profit & Loss Expectations
    profit_expected = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    profit_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    loss_expected = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    loss_recent = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    pl_ratio = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Calculations
    rate_difference = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pl_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Notes
    comments = models.TextField(blank=True)

    # Performance
    max_profit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_profit_loss = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.stock.symbol} - {self.user.username}"

    @property
    def total_cost(self):
        """Calculate total cost of the trade (quantity * buying_price)."""
        return self.quantity * self.buying_price

    @property
    def current_price(self):
        """Get current market price from associated stock."""
        return self.stock.current_price if self.stock else None

    @property
    def current_value(self):
        """Calculate current value of the trade (quantity * current_price)."""
        if self.current_price:
            return self.quantity * self.current_price
        return None

    @property
    def unrealized_pl(self):
        """
        'pl' 'profit and loss'.
        This property computes the unrealized profit or loss of the trade.
       
        Formula: (current market price * quantity) - (buying price * quantity)
        i.e. unrealized_pl = current_value - total_cost
        """
        if self.current_value is not None:
            return self.current_value - self.total_cost
        return None 

    @property
    def pl_percent(self):
        """Calculate profit/loss percentage."""
        if self.total_cost and self.unrealized_pl is not None:
            return round((self.unrealized_pl / self.total_cost) * 100, 2)
        return 0

    def save(self, *args, **kwargs):
        """
        Override the save method to automatically calculate 
        profit and loss related fields whenever the model is saved.
        
        This method updates several attributes such as:
        - profit_expected
        - profit_percent
        - loss_expected
        - pl_ratio
        - rate_difference
        - loss_recent
        
        The calculation depends on fields like:
        - self.mtp (Maximum Target Price)
        - self.msl (Maximum Stop Loss)
        - self.buying_price
        - self.quantity
        - self.current_price (property, not a field)
        """
        
        # --- PROFIT EXPECTED ---
        # If the field "mtp" (Maximum Target Price) is set (not None, not 0, not empty)
        if self.mtp:
            # Calculate expected profit: (mtp - buying_price) * quantity
            # mtp is the price at which you plan to sell for maximum profit
            self.profit_expected = (self.mtp - self.buying_price) * self.quantity
            
            # Next, calculate the percent profit.
            # This shows how much percentage return you make if you sell at mtp.
            if self.buying_price:
                # Formula: ((mtp - buying_price) / buying_price) * 100 (rounded to 2 decimal places)
                self.profit_percent = round(((self.mtp - self.buying_price) / self.buying_price) * 100, 2)
            else:
                # If buying price is zero/not set, can't calculate percent.
                self.profit_percent = None
        else:
            # If mtp is not set, nullify the profit fields.
            self.profit_expected = None
            self.profit_percent = None

        # --- LOSS EXPECTED ---
        # If "msl" (Maximum Stop Loss) is set (where to sell to cut losses)
        if self.msl:
            # Calculate the maximum loss if price falls to msl and you exit:
            # (buying_price - msl) * quantity
            self.loss_expected = (self.buying_price - self.msl) * self.quantity
        else:
            # If not set, no loss expected can be calculated
            self.loss_expected = None

        # --- P/L RATIO ---
        # If all the below are set, calculate the Profit/Loss ratio:
        # - mtp (target/expected sell price)
        # - msl (stop-loss price)
        # - buying_price
        if self.mtp and self.msl and self.buying_price:
            # Calculate profit per share (how much you'd make for each share if you hit mtp)
            profit_per_share = self.mtp - self.buying_price

            # Calculate loss per share (how much you'd lose for each share if you hit msl)
            loss_per_share = self.buying_price - self.msl

            # Only define ratio if potential loss per share is positive (you can really lose money)
            if loss_per_share > 0:
                # The profit-to-loss ratio: how much potential profit vs potential loss
                # For example, 2 means your possible profit is twice the possible loss
                self.pl_ratio = round(profit_per_share / loss_per_share, 2)
            else:
                # If you'd not lose money (maybe msl >= buying_price), ratio is undefined
                self.pl_ratio = None
        else:
            # If not all are set, cannot calculate ratio
            self.pl_ratio = None

        # --- RATE DIFFERENCE ---
        # Calculate the current price difference over your buy price
        if self.current_price:
            # If current (market) price is available, subtract what you paid
            self.rate_difference = self.current_price - self.buying_price
        else:
            # If no current price, leave blank (None)
            self.rate_difference = None

        # --- RECENT LOSS ---
        # If you set a stop loss and current price exists:
        if self.msl and self.current_price:
            # If the current price is lower than your buy price, there is an unrealized loss
            if self.current_price < self.buying_price:
                # Calculate how much you'd lose if sold now (it hasn't hit msl, but is below buy)
                self.loss_recent = (self.buying_price - self.current_price) * self.quantity
            else:
                # If price didn't go below buying, no unrealized recent loss
                self.loss_recent = None
        else:
            # If you didn't set msl, or don't have current price, cannot compute recent loss
            self.loss_recent = None

        # NOTE:
        # Fields like max_profit and min_profit_loss require historical data (price history)
        # so these are not calculated automatically here.

        # Finally, call the original save method to update the object in the database
        super().save(*args, **kwargs)
