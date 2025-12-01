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
            dropZone.classList.add('border-secondary', 'bg-base-200', 'scale-105');
        }
        
        function unhighlight(e) {
            dropZone.classList.remove('border-secondary', 'bg-base-200', 'scale-105');
        }
        
        // Manejar archivos soltados
        dropZone.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = Array.from(dt.files);
            handleFiles(files);
        }
        
        // Botón para seleccionar archivos
        selectFilesBtn.addEventListener('click', function(e) {
            e.stopPropagation(); // Evitar que se propague al dropZone
            fileInput.click();
        });
        
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
                        <div class="flex-shrink-0">
                            <i class="fas fa-file-excel text-green-600 text-4xl"></i>
                        </div>
                        <div class="flex-1">
                            <p class="font-semibold text-gray-800">${file.name}</p>
                            <p class="text-sm text-gray-600">
                                <i class="fas fa-weight-hanging text-xs mr-1"></i>
                                ${fileSizeMB} MB
                            </p>
                        </div>
                        <button type="button" onclick="removeFile(${index})" class="btn btn-circle btn-ghost btn-sm text-error hover:bg-error hover:text-white" title="Eliminar archivo">
                            <i class="fas fa-times text-lg"></i>
                        </button>
                    `;
                    filesList.appendChild(fileCard);
                });
                
                // Mostrar opción de agregar más SOLO si no ha llegado al límite
                if (selectedFiles.length < MAX_FILES) {
                    const addMoreCard = document.createElement('div');
                    addMoreCard.className = 'flex items-center justify-center p-3 border-2 border-dashed border-green-300 rounded-lg bg-green-50 hover:bg-green-100 transition-colors cursor-pointer';
                    addMoreCard.innerHTML = `
                        <button type="button" class="flex items-center gap-2 text-green-700 font-semibold">
                            <i class="fas fa-plus-circle text-xl"></i>
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
        
        // Hacer clic en la zona para abrir selector (solo si está visible el dropZoneContent)
        dropZone.addEventListener('click', function(e) {
            if (!dropZoneContent.classList.contains('hidden')) {
                fileInput.click();
            }
        });

        // Manejar envío del formulario con indicadores visuales
        const uploadForm = document.getElementById('uploadForm');
        uploadForm.addEventListener('submit', function(e) {
            // Deshabilitar el botón para evitar doble clic
            submitBtn.disabled = true;
            
            // Cambiar el ícono y texto del botón
            const submitBtnIcon = document.getElementById('submitBtnIcon');
            const submitBtnSpinner = document.getElementById('submitBtnSpinner');
            const uploadProgress = document.getElementById('uploadProgress');
            
            submitBtnIcon.classList.add('hidden');
            submitBtnSpinner.classList.remove('hidden');
            submitBtnText.textContent = 'Subiendo archivos...';
            
            // Mostrar barra de progreso
            uploadProgress.classList.remove('hidden');
            
            // Simular progreso (ya que no podemos capturar el progreso real sin AJAX)
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
            
            // El formulario se enviará normalmente
        });