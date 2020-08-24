from django.shortcuts import render, get_object_or_404
from .models import Item, Order, OrderItem
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect
from django.contrib import messages
from .forms import CheckoutForm
from django.utils import timezone
# Create your views here.
class HomeView(ListView):
    model = Item
    template_name = 'home.html'

class CheckoutView(View):
    def get(self, *args, **kwargs):
        form = CheckoutForm()
        context ={
            'form' : form,
        }
        return render(self.request,"checkout.html", context)

class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("/")

def products(request):
    context={
        'items' : Item.objects.all()
    }
    return render(request, "product.html", context)


class ItemDetailView(DetailView):
    model = Item
    template_name = "product.html"

def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created= OrderItem.objects.get_or_create(
        item = item, 
        user = request.user,
        ordered = False,
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
            return redirect("core:product", slug = slug)
        else:
            messages.info(request, "This item was added to your cart.")
            order.items.add(order_item)
            return redirect("core:product", slug = slug)
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user = request.user, ordered_date = ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart")
        return redirect("core:product", slug = slug)

def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item = item,
                ordered = False,
                user =request.user,
            )[0] 
            order.items.remove(order_item)
            messages.info(request, "This item was remove from your cart")
        else:
            # add a massage saying the user doesn't have an item
            messages.info(request, "This item was not in your cart")
            redirect("core:product", slug = slug)
    else:
        # add a massage saying the user doesn't have an order
        messages.info(request, "You do not have an activte order")
        redirect("core:product", slug = slug)

    return redirect("core:product", slug = slug)
