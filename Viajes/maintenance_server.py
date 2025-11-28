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
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @keyframes fly {
            0% { transform: translateX(-100px) translateY(20px) rotate(-20deg); opacity: 0; }
            20% { opacity: 1; }
            80% { opacity: 1; }
            100% { transform: translateX(100vw) translateY(-100px) rotate(10deg); opacity: 0; }
        }
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
        }
        .plane-animation {
            animation: fly 8s ease-in-out infinite;
        }
        .float-animation {
            animation: float 3s ease-in-out infinite;
        }
    </style>
</head>
<body class="bg-gradient-to-br from-green-50 to-emerald-100 min-h-screen flex items-center justify-center p-4 overflow-hidden relative">
    <!-- Aviones animados en el fondo -->
    <div class="fixed top-1/4 left-0 w-full pointer-events-none">
        <i class="fas fa-plane text-green-600 text-6xl plane-animation absolute opacity-30"></i>
    </div>
    
    <div class="text-center max-w-2xl relative z-10">
        <div class="mb-8 float-animation">
            <!-- Icono de avión y herramientas -->
            <div class="relative inline-block">
                <i class="fas fa-plane-departure text-green-600 text-8xl mb-4 block"></i>
                <i class="fas fa-tools text-green-700 text-3xl absolute bottom-0 right-0 bg-white rounded-full p-2 shadow-lg"></i>
            </div>
        </div>
        
        <h1 class="text-6xl font-bold text-green-600 mb-4">
            <i class="fas fa-wrench mr-2"></i>
            En Mantenimiento
        </h1>
        <h2 class="text-3xl font-bold text-gray-800 mb-4">Estamos Mejorando el Sistema</h2>
        <p class="text-xl text-gray-600 mb-8">
            El sistema de Viajes INM está temporalmente fuera de servicio para realizar actualizaciones y mejoras.
        </p>
        
        <div class="bg-white rounded-lg shadow-lg p-8 mb-8">
            <div class="flex items-center justify-center gap-2 mb-4">
                <i class="fas fa-circle-info text-green-600 text-2xl"></i>
                <h3 class="text-lg font-semibold text-gray-700">¿Qué está pasando?</h3>
            </div>
            <ul class="text-left text-gray-600 space-y-3">
                <li class="flex items-start gap-3">
                    <i class="fas fa-cog text-green-600 mt-1 text-xl"></i>
                    <span>Estamos aplicando actualizaciones importantes</span>
                </li>
                <li class="flex items-start gap-3">
                    <i class="fas fa-database text-green-600 mt-1 text-xl"></i>
                    <span>Realizando migraciones de base de datos</span>
                </li>
                <li class="flex items-start gap-3">
                    <i class="fas fa-rocket text-green-600 mt-1 text-xl"></i>
                    <span>El sistema volverá pronto con mejoras</span>
                </li>
            </ul>
        </div>
        
        <div class="bg-green-100 border-2 border-green-300 rounded-lg p-6 mb-8">
            <p class="text-lg font-semibold text-green-700 mb-2">
                <i class="fas fa-clock mr-2"></i>
                Tiempo estimado
            </p>
            <p class="text-gray-700">Normalmente estos mantenimientos toman entre 5 a 15 minutos</p>
        </div>
        
        <div class="flex flex-col gap-4 justify-center items-center">
            <div class="flex gap-2 items-center text-gray-600">
                <div class="loading loading-spinner loading-md text-green-600"></div>
                <span>Esta página se recargará automáticamente cada 30 segundos</span>
            </div>
            <button onclick="location.reload()" class="btn bg-green-600 hover:bg-green-700 text-white border-green-600 btn-lg gap-2">
                <i class="fas fa-rotate-right text-xl"></i>
                Reintentar Ahora
            </button>
        </div>
        
        <div class="mt-12 text-gray-500 text-sm">
            <p>
                <i class="fas fa-heart text-green-600"></i>
                Gracias por tu paciencia
            </p>
            <p class="mt-2">
                <i class="fas fa-headset text-green-600 mr-1"></i>
                ¿Urgente? Contacta al administrador del sistema
            </p>
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
