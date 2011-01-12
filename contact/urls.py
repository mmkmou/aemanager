from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('contact.views',
    url(regex=r'^$',
        view='contact_search',
        name='contact_search'),
    url(regex=r'^(?P<id>\d+)/$',
        view='contact_detail',
        name='contact_detail'),
    url(regex=r'^delete/(?P<id>\d+)/$',
        view='contact_delete',
        name='contact_delete'),
    url(regex=r'^add/$',
        view='contact_create_or_edit',
        name='contact_add'),
    url(regex=r'^edit/(?P<id>\d+)/$',
        view='contact_create_or_edit',
        name='contact_edit'),
)