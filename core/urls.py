from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('core.views',
    url(
        regex=r'^$',
        view='settings_edit',
        name='settings_edit'),
    url(
        regex=r'^logo_overview/$',
        view='logo_overview',
        name='logo_overview'),
    url(
        regex=r'^logo_delete/$',
        view='logo_delete',
        name='logo_delete'),
    url(
        regex=r'^change_password/$',
        view='change_password',
        name='change_password'),
    url(
        regex=r'^subscribe/$',
        view='subscribe',
        name='subscribe'),
    url(
        regex=r'^subscription_paid/$',
        view='subscription_paid',
        name='subscription_paid'),
    url(
        regex=r'^paypal_ipn/$',
        view='paypal_ipn',
        name='paypal_ipn'),
    url(
        regex=r'^unregister/$',
        view='unregister',
        name='unregister'),
)
