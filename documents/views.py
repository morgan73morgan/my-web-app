from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import Document, DocumentCategory
from .forms import DocumentForm
from .utils import send_document_status_email


class DocumentListView(LoginRequiredMixin, ListView):
    model = Document
    template_name = 'documents/document_list.html'
    context_object_name = 'documents'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('patient', 'category', 'uploaded_by')

        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(patient__first_name__icontains=search_query) |
                Q(patient__last_name__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )

        # Filtering by category
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Document Management')
        context['categories'] = DocumentCategory.objects.all()
        return context


class DocumentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = 'documents.add_document'
    model = Document
    form_class = DocumentForm
    template_name = 'documents/document_form.html'
    success_url = reverse_lazy('documents:document_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Upload New Document')
        return context

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, _('Document uploaded successfully.'))
        return super().form_valid(form)


class DocumentDetailView(LoginRequiredMixin, DetailView):
    model = Document
    template_name = 'documents/document_detail.html'
    context_object_name = 'document'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.object.title
        return context


class DocumentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = 'documents.change_document'
    model = Document
    form_class = DocumentForm
    template_name = 'documents/document_form.html'
    context_object_name = 'document'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Edit Document: {}').format(self.object.title)
        return context

    def get_success_url(self):
        messages.success(self.request, _('Document updated successfully.'))
        return reverse_lazy('documents:document_detail', kwargs={'pk': self.object.pk})


class DocumentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = 'documents.delete_document'
    model = Document
    template_name = 'documents/document_confirm_delete.html'
    success_url = reverse_lazy('documents:document_list')
    context_object_name = 'document'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Delete Document: {}').format(self.object.title)
        return context

    def form_valid(self, form):
        messages.success(self.request, _('Document deleted successfully.'))
        return super().form_valid(form)


@login_required
@require_POST
@permission_required('documents.approve_document', raise_exception=True)
def approve_document(request, pk):
    """
    Approves a document, changing its status to 'Approved'.
    """
    document = get_object_or_404(Document, pk=pk)
    if document.status == 'pending_approval':
        document.status = 'approved'
        document.approved_by = request.user
        document.approved_at = timezone.now()
        document.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])
        # Отправить уведомление пациенту (и врачу, если нужно)
        if document.patient and hasattr(document.patient, 'email') and document.patient.email:
            send_document_status_email(document, 'approved', document.patient.email)
        messages.success(request, _('Document "{title}" has been approved.').format(title=document.title))
    else:
        messages.warning(request, _('This document cannot be approved in its current state.'))
    return redirect('documents:document_detail', pk=document.pk)


@login_required
@require_POST
@permission_required('documents.change_document', raise_exception=True)
def archive_document(request, pk):
    """
    Archives a document, changing its status to 'Archived'.
    """
    document = get_object_or_404(Document, pk=pk)
    if document.status in ['approved', 'draft']:
        document.status = 'archived'
        document.save(update_fields=['status', 'updated_at'])
        # Отправить уведомление пациенту (и врачу, если нужно)
        if document.patient and hasattr(document.patient, 'email') and document.patient.email:
            send_document_status_email(document, 'archived', document.patient.email)
        messages.success(request, _('Document "{title}" has been archived.').format(title=document.title))
    else:
        messages.warning(request, _('This document cannot be archived in its current state.'))
    return redirect('documents:document_detail', pk=document.pk)
