 const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('id_archivo');
        const dropZoneContent = document.getElementById('dropZoneContent');
        const filesList = document.getElementById('filesList');
        const submitBtn = document.getElementById('submitBtn');
        const submitBtnText = document.getElementById('submitBtnText');
        const selectFilesBtn = document.getElementById('selectFilesBtn');
        
        let selectedFiles = [];
        const MAX_FILES = 2;
        const MAX_SIZE = 10 * 1024 * 1024; // 10MB
        
        // Prevenir comportamiento por defecto
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        // Destacar zona cuando se arrastra sobre ella
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight(e) {
            dropZone.classList.add('ds-dropzone-over');
        }

        function unhighlight(e) {
            dropZone.classList.remove('ds-dropzone-over');
        }
        
        // Manejar archivos soltados
        dropZone.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = Array.from(dt.files);
            handleFiles(files);
        }
        
        // Botón para seleccionar archivos (opcional: el dropzone ya es un <label>
        // asociado a #id_archivo, así que este botón puede no existir en la plantilla)
        if (selectFilesBtn) {
            selectFilesBtn.addEventListener('click', function(e) {
                e.stopPropagation(); // Evitar que se propague al dropZone
                fileInput.click();
            });
        }
        
        // Manejar selección de archivos con click
        fileInput.addEventListener('change', function(e) {
            e.stopPropagation(); // Evitar propagación
            const files = Array.from(this.files);
            handleFiles(files);
        });
        
        // Procesar archivos
        function handleFiles(files) {
            // Verificar límite de archivos
            if (selectedFiles.length + files.length > MAX_FILES) {
                alert(`⚠️ Solo puedes cargar un máximo de ${MAX_FILES} archivos`);
                return;
            }
            
            files.forEach(file => {
                // Validar tipo
                const validTypes = ['.xlsx', '.xls', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel'];
                const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
                
                if (!validTypes.includes(fileExtension) && !validTypes.includes(file.type)) {
                    alert(`⚠️ "${file.name}" no es un archivo Excel válido`);
                    return;
                }
                
                // Validar tamaño
                if (file.size > MAX_SIZE) {
                    alert(`⚠️ "${file.name}" es demasiado grande. Máximo 10MB`);
                    return;
                }
                
                // Agregar a la lista
                selectedFiles.push(file);
            });
            
            updateUI();
        }
        
        // Actualizar interfaz
        function updateUI() {
            if (selectedFiles.length > 0) {
                dropZoneContent.classList.add('hidden');
                filesList.classList.remove('hidden');
                filesList.innerHTML = '';
                
                selectedFiles.forEach((file, index) => {
                    const fileSizeMB = (file.size / 1024 / 1024).toFixed(2);
                    
                    const fileCard = document.createElement('div');
                    fileCard.className = 'flex items-center gap-3 p-3 bg-green-50 border border-green-200 rounded-lg';
                    fileCard.innerHTML = `
                        <div class="flex-shrink-0" style="color:var(--ds-success);">
                            <svg class="ds-icon" aria-hidden="true" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M9 13h6M9 17h6"/></svg>
                        </div>
                        <div class="flex-1">
                            <p class="font-semibold text-gray-800">${file.name}</p>
                            <p class="text-sm text-gray-600">${fileSizeMB} MB</p>
                        </div>
                        <button type="button" onclick="removeFile(${index})" class="ds-btn ds-btn-icon ds-btn-sm ds-btn-danger-ghost" aria-label="Eliminar archivo" title="Eliminar archivo">
                            <svg class="ds-icon ds-icon-sm" aria-hidden="true" viewBox="0 0 24 24"><path d="M18 6 6 18M6 6l12 12"/></svg>
                        </button>
                    `;
                    filesList.appendChild(fileCard);
                });
                
                // Mostrar opción de agregar más SOLO si no ha llegado al límite
                if (selectedFiles.length < MAX_FILES) {
                    const addMoreCard = document.createElement('div');
                    addMoreCard.className = 'flex items-center justify-center p-3 border-2 border-dashed border-green-300 rounded-lg bg-green-50 hover:bg-green-100 transition-colors cursor-pointer';
                    addMoreCard.innerHTML = `
                        <button type="button" class="flex items-center gap-2 text-green-700 font-semibold" style="background:none; border:0; cursor:pointer;">
                            <svg class="ds-icon ds-icon-sm" aria-hidden="true" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>
                            Agregar otro archivo (${selectedFiles.length}/${MAX_FILES})
                        </button>
                    `;
                    addMoreCard.onclick = function(e) {
                        e.stopPropagation();
                        fileInput.click();
                    };
                    filesList.appendChild(addMoreCard);
                }
                
                submitBtn.disabled = false;
                submitBtnText.textContent = `Cargar ${selectedFiles.length} archivo${selectedFiles.length > 1 ? 's' : ''}`;
            } else {
                dropZoneContent.classList.remove('hidden');
                filesList.classList.add('hidden');
                submitBtn.disabled = true;
                submitBtnText.textContent = 'Cargar Archivos Excel';
            }
            
            // Actualizar el input file con los archivos seleccionados
            updateFileInput();
        }
        
        // Actualizar el input file
        function updateFileInput() {
            const dt = new DataTransfer();
            selectedFiles.forEach(file => dt.items.add(file));
            fileInput.files = dt.files;
        }
        
        // Eliminar archivo
        function removeFile(index) {
            selectedFiles.splice(index, 1);
            updateUI();
        }
        
        // Nota: no llamamos fileInput.click() aquí. El dropzone es un <label for="id_archivo">,
        // así que el click sobre la zona abre el selector de archivos de forma nativa.
        // Añadir un fileInput.click() manual provocaría que el diálogo se abriera dos veces.

        // Manejar envío del formulario con modal de fecha + indicadores visuales
        const uploadForm = document.getElementById('uploadForm');
        const modalFechaCarga = document.getElementById('modalFechaCarga');
        const inputFechaCarga = document.getElementById('inputFechaCarga');
        const fechaCargaHidden = document.getElementById('fecha_carga_seleccionada');
        const formFechaCarga = document.getElementById('formFechaCarga');
        const btnCancelarFechaCarga = document.getElementById('btnCancelarFechaCarga');

        // Flag para saber si la fecha ya fue confirmada
        let fechaConfirmada = false;

        // Devuelve la fecha de hoy en formato YYYY-MM-DD (hora local del navegador)
        function fechaHoyLocal() {
            const hoy = new Date();
            const yyyy = hoy.getFullYear();
            const mm = String(hoy.getMonth() + 1).padStart(2, '0');
            const dd = String(hoy.getDate()).padStart(2, '0');
            return `${yyyy}-${mm}-${dd}`;
        }

        // Interceptar submit del form principal: abrir modal si falta confirmar fecha
        uploadForm.addEventListener('submit', function(e) {
            if (!fechaConfirmada) {
                e.preventDefault();

                // Precargar con la fecha de hoy
                inputFechaCarga.value = fechaHoyLocal();
                modalFechaCarga.showModal();

                // Foco al input para permitir teclear y/o presionar Enter
                setTimeout(() => inputFechaCarga.focus(), 50);
                return;
            }

            // Ya hay fecha confirmada: continuar con el flujo de progreso visual
            submitBtn.disabled = true;

            const submitBtnIcon = document.getElementById('submitBtnIcon');
            const submitBtnSpinner = document.getElementById('submitBtnSpinner');
            const uploadProgress = document.getElementById('uploadProgress');

            submitBtnIcon.classList.add('hidden');
            submitBtnSpinner.classList.remove('hidden');
            submitBtnText.textContent = 'Subiendo archivos...';

            uploadProgress.classList.remove('hidden');

            let progress = 0;
            const progressBar = document.getElementById('progressBar');
            const progressText = document.getElementById('progressText');

            const interval = setInterval(() => {
                if (progress < 90) {
                    progress += Math.random() * 15;
                    if (progress > 90) progress = 90;

                    progressBar.value = progress;

                    if (progress < 30) {
                        progressText.textContent = 'Validando archivos...';
                    } else if (progress < 60) {
                        progressText.textContent = 'Subiendo al servidor...';
                    } else {
                        progressText.textContent = 'Procesando datos...';
                    }
                }
            }, 300);
        });

        // Submit del form del modal: valida fecha, la pone en el hidden y envía el form real.
        // Enter en el input también dispara este submit (comportamiento nativo del form).
        formFechaCarga.addEventListener('submit', function(e) {
            e.preventDefault();

            const fecha = inputFechaCarga.value;
            if (!fecha) {
                alert('⚠️ Selecciona una fecha para continuar.');
                inputFechaCarga.focus();
                return;
            }

            fechaCargaHidden.value = fecha;
            fechaConfirmada = true;
            modalFechaCarga.close();

            // Reenviar el form principal
            uploadForm.requestSubmit();
        });

        // Cancelar cierra el modal y resetea el flag (el usuario puede reintentar)
        btnCancelarFechaCarga.addEventListener('click', function() {
            fechaConfirmada = false;
            modalFechaCarga.close();
        });