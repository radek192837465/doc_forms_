from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from docxtpl import DocxTemplate
import json, os, io
from .models import UploadedFile
from django.conf import settings

#Rejestracja
def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login_view")
    else:
        form = UserCreationForm()
    return render(request, "doc_form/register.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("index")
    else:
        form = AuthenticationForm()
    return render(request, "doc_form/login.html", {"form": form})

def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("login_view")
    
# views.py
def index(request):
    files = UploadedFile.objects.all()
    return render(request, 'doc_form/index.html', {'files': files})

def delete_file_view(request, file_id):
    if request.method == 'POST':
        file_to_delete = UploadedFile.objects.get(file_id=file_id)
        # Usuń plik z lokalizacji static/files/
        file_path = 'static/files/'+ str(file_to_delete.file_id)+'.docx'
        if os.path.exists(file_path):
            os.remove(file_path)

        # Usuń obiekt bazy danych
        file_to_delete.delete()
    files = UploadedFile.objects.all()
    return render(request, 'doc_form/index.html', {'files': files})

def form_view(request, file_id):
    # Pobierz obiekt UploadedFile na podstawie file_id
    uploaded_file = get_object_or_404(UploadedFile, file_id=file_id)
    
    # Pobierz dane JSON z pola json_content
    form_data = uploaded_file.json_content
    file_name = uploaded_file.file_name
    if request.method == 'POST':
        form_values = {}
        for field in form_data['fields']:
            form_values[field['label']] = request.POST.get(field['name'])#jak dodać .encode('utf-8')
            # Wypełnij odpowiedni plik

        doc = DocxTemplate('static/files/'+ str(uploaded_file.file_id)+'.docx')
        if doc:
            doc.render(form_values)
            
            # Utwórz obiekt BytesIO w pamięci
            file_stream = io.BytesIO()

            # Zapisz dokument do obiektu BytesIO
            doc.save(file_stream)

            # Ustaw wskaźnik na początek strumienia
            file_stream.seek(0)
            if file_stream:
                
                response = HttpResponse(file_stream.read(), content_type="application/octet-stream")
                response['Content-Disposition'] = f'attachment; filename={str(uploaded_file.file_name)+"-uzupelniony.docx"}'
                return response 
            raise Http404

        form_values = json.dumps(form_values, ensure_ascii=False).encode('utf8')
        # Tutaj możesz wypełnić odpowiedni plik na podstawie form_values
            
        return HttpResponse(form_values, content_type='application/json')
    
    return render(request, 'doc_form/form_template.html', {'form_data': form_data, 'file_name': file_name})

@login_required(login_url='/login')
def form_new_doc_view(request):
    if request.method == 'POST':
        # Pobierz dane z formularza
        title = request.POST.get('title')
        describe = request.POST.get('describe')
        doc_file = request.FILES.get('doc_file')
        
        # Pobierz dane rubryk z formularza
        fields = []
        for key, value in request.POST.items():
            if key.startswith('label_'):
                index = key.split('_')[1]
                label = value
                field_type = request.POST.get('type_' + index, 'text')  # Default type is text
                field_name = 'field_' + index
                fields.append({'label': label, 'type': field_type, 'name': field_name})
        
        # Utwórz słownik z danymi rubryk
        form_data = {'fields': fields}

        # Zapisz dane do modelu UploadedFile
        uploaded_file = UploadedFile.objects.create(
            file_name=title,
            file_describe=describe,
            json_content=form_data
        )

        # Zapisz plik .docs w katalogu static/files/
        file_path = default_storage.save('static/files/' + str(uploaded_file.file_id) +'.'+ doc_file.name.split('.')[-1], ContentFile(doc_file.read()))

        return redirect('index')

    return render(request, 'doc_form/form_new_doc.html')

@login_required(login_url='/login')
def edit_doc_view(request, file_id):
    # Pobierz istniejący wpis na podstawie doc_id
    existing_doc = get_object_or_404(UploadedFile, file_id=file_id)
    if existing_doc:
        if request.method == 'POST':
            # Pobierz dane z formularza
            title = request.POST.get('title')
            describe = request.POST.get('describe')
            doc_file = request.FILES.get('doc_file')
            
            # Pobierz dane rubryk z formularza
            fields = []
            for key, value in request.POST.items():
                if key.startswith('label_'):
                    index = key.split('_')[1]
                    label = value
                    field_type = request.POST.get('type_' + index, 'text')  # Default type is text
                    field_name = 'field_' + index
                    fields.append({'label': label, 'type': field_type, 'name': field_name})
            
            # Utwórz słownik z danymi rubryk
            form_data = {'fields': fields}

            # Zaktualizuj istniejący wpis
            existing_doc.file_name = title
            existing_doc.file_describe = describe
            existing_doc.json_content = form_data
            
            if doc_file:
                # Zapisz nowy plik .docs w katalogu static/files/
                file_path = default_storage.save('static/files/' + str(existing_doc.file_id) +'.'+ doc_file.name.split('.')[-1], ContentFile(doc_file.read()))
            
            existing_doc.save()

            return redirect('index')

    return render(request, 'doc_form/form_edit_doc.html', {'existing_doc': existing_doc})
