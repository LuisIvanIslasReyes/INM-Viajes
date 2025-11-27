"""
Servidor simple de mantenimiento
Ejecuta esto en el puerto 8002 cuando detengas el servidor principal
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

# Cambiar al directorio donde está el HTML de mantenimiento
os.chdir(os.path.dirname(os.path.abspath(__file__)))

class MaintenanceHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        """Siempre devuelve la página de mantenimiento"""
        self.send_response(503)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Retry-After', '300')  # Reintentar en 5 minutos
        self.end_headers()
        
        html = """<!DOCTYPE html>
<html lang="es" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="30">
    <title>Mantenimiento | Viajes INM</title>
    <link href="https://cdn.jsdelivr.net/npm/daisyui@4.12.14/dist/full.min.css" rel="stylesheet" type="text/css" />
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen flex items-center justify-center p-4">
    <div class="text-center max-w-2xl">
        <div class="mb-8">
            <!-- Icono de herramientas -->
            <svg xmlns="http://www.w3.org/2000/svg" class="h-32 w-32 mx-auto text-info opacity-80 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
        </div>
        
        <h1 class="text-6xl font-bold text-info mb-4">🔧 En Mantenimiento</h1>
        <h2 class="text-3xl font-bold text-gray-800 mb-4">Estamos Mejorando el Sistema</h2>
        <p class="text-xl text-gray-600 mb-8">
            El sistema de Viajes INM está temporalmente fuera de servicio para realizar actualizaciones y mejoras.
        </p>
        
        <div class="bg-white rounded-lg shadow-lg p-8 mb-8">
            <div class="flex items-center justify-center gap-2 mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-info" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3 class="text-lg font-semibold text-gray-700">¿Qué está pasando?</h3>
            </div>
            <ul class="text-left text-gray-600 space-y-3">
                <li class="flex items-start gap-2">
                    <span class="text-info mt-1 text-xl">⚙️</span>
                    <span>Estamos aplicando actualizaciones importantes</span>
                </li>
                <li class="flex items-start gap-2">
                    <span class="text-info mt-1 text-xl">⚙️</span>
                    <span>Realizando migraciones de base de datos</span>
                </li>
                <li class="flex items-start gap-2">
                    <span class="text-info mt-1 text-xl">⚙️</span>
                    <span>El sistema volverá pronto con mejoras</span>
                </li>
            </ul>
        </div>
        
        <div class="bg-info/10 rounded-lg p-6 mb-8">
            <p class="text-lg font-semibold text-info mb-2">⏱️ Tiempo estimado</p>
            <p class="text-gray-700">Normalmente estos mantenimientos toman entre 5 a 15 minutos</p>
        </div>
        
        <div class="flex flex-col gap-4 justify-center items-center">
            <div class="flex gap-2 items-center text-gray-600">
                <div class="loading loading-spinner loading-md text-info"></div>
                <span>Esta página se recargará automáticamente cada 30 segundos</span>
            </div>
            <button onclick="location.reload()" class="btn btn-info btn-lg gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Reintentar Ahora
            </button>
        </div>
        
        <div class="mt-12 text-gray-500 text-sm">
            <p>Gracias por tu paciencia 🙏</p>
            <p class="mt-2">¿Urgente? Contacta al administrador del sistema</p>
        </div>
    </div>
</body>
</html>"""
        
        self.wfile.write(html.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Silenciar logs del servidor"""
        pass

if __name__ == '__main__':
    PORT = 8002
    print(f"🔧 Servidor de mantenimiento iniciado en http://localhost:{PORT}")
    print("⏹️  Presiona Ctrl+C para detener")
    
    server = HTTPServer(('0.0.0.0', PORT), MaintenanceHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ Servidor de mantenimiento detenido")
        server.shutdown()
