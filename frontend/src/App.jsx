import { useState, useEffect } from 'react';
import Auth from './Auth';

function App() {
  const [articulos, setArticulos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [mostrarAuth, setMostrarAuth] = useState(false);
  const [usuario, setUsuario] = useState(null);
  const [carrito, setCarrito] = useState([]);
  const [mostrarCarrito, setMostrarCarrito] = useState(false);
  const [favoritos, setFavoritos] = useState([]);

  useEffect(() => {
    const usuarioGuardado = localStorage.getItem('usuario');
    if (usuarioGuardado) setUsuario(JSON.parse(usuarioGuardado));
    const carritoGuardado = localStorage.getItem('carrito');
    if (carritoGuardado) setCarrito(JSON.parse(carritoGuardado));
    const favsGuardados = localStorage.getItem('favoritos');
    if (favsGuardados) setFavoritos(JSON.parse(favsGuardados));
    
    fetch('http://localhost:8000/getArticulos')
      .then(res => res.json())
      .then(data => { setArticulos(data); setCargando(false); })
      .catch(err => { console.error("Error:", err); setCargando(false); });
  }, []);

  useEffect(() => { localStorage.setItem('carrito', JSON.stringify(carrito)); }, [carrito]);
  useEffect(() => { localStorage.setItem('favoritos', JSON.stringify(favoritos)); }, [favoritos]);

  const cerrarSesion = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('usuario');
    setUsuario(null);
  };

  const toggleFavorito = (id) => {
    setFavoritos(favoritos.includes(id) ? favoritos.filter(f => f !== id) : [...favoritos, id]);
  };

  const añadirAlCarrito = (articulo) => {
    setCarrito([...carrito, articulo]);
  };

  const comprarCarrito = async () => {
    if (!usuario) {
      setMostrarCarrito(false);
      setMostrarAuth(true);
      return;
    }
    const token = localStorage.getItem('token');
    let errores = 0;

    for (const item of carrito) {
      const datosCompra = { articulo_id: item.articulo_id, cantidad: 1, tipo_movimiento: "venta", coste_total: item.precio_unitario };
      try {
        const res = await fetch('http://localhost:8000/setCompraUserId', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify(datosCompra)
        });
        if (!res.ok) errores++;
      } catch (error) { errores++; }
    }

    if (errores === 0) {
      alert("Su compra se ha procesado con elegancia. ¡Gracias!");
      setCarrito([]);
      setMostrarCarrito(false);
    } else {
      alert("Hubo un contratiempo con su pedido. Inténtelo de nuevo.");
    }
  };

  const totalCarrito = carrito.reduce((sum, item) => sum + parseFloat(item.precio_unitario), 0).toFixed(2);

  return (
    <div className="min-h-screen bg-[#F7F5F0] text-[#2C241B] relative pb-20">
      
      {/* --- MODAL LOGIN --- */}
      {mostrarAuth && <Auth onCerrar={() => setMostrarAuth(false)} onLogin={(user) => { setUsuario(user); setMostrarAuth(false); }} />}

      {/* --- MODAL CARRITO --- */}
      {mostrarCarrito && (
        <div className="fixed inset-0 bg-[#2C241B]/40 backdrop-blur-sm flex justify-end z-50 transition-opacity">
          <div className="bg-[#F7F5F0] w-full max-w-md h-full shadow-2xl p-8 flex flex-col relative overflow-hidden animate-slide-in-right">
            <button onClick={() => setMostrarCarrito(false)} className="absolute top-6 right-6 text-2xl text-[#2C241B] hover:scale-110 transition-transform">✕</button>
            <h2 className="text-3xl font-serif italic mb-8 border-b border-[#2C241B]/20 pb-4">Su Selección</h2>
            
            <div className="flex-grow overflow-y-auto pr-4 flex flex-col gap-6">
              {carrito.length === 0 ? (
                <p className="text-stone-500 italic">No hay tesoros en su bolsa aún.</p>
              ) : (
                carrito.map((item, i) => (
                  <div key={i} className="flex justify-between items-center group">
                    <span className="font-medium tracking-wide text-sm uppercase">{item.nombre}</span>
                    <span className="font-serif text-lg">{item.precio_unitario}€</span>
                  </div>
                ))
              )}
            </div>

            {carrito.length > 0 && (
              <div className="pt-6 border-t border-[#2C241B]/20 mt-6">
                <div className="flex justify-between items-center mb-6">
                  <span className="text-sm tracking-widest uppercase">Total</span>
                  <span className="text-3xl font-serif">{totalCarrito}€</span>
                </div>
                <button onClick={comprarCarrito} className="w-full bg-[#2C241B] text-[#F7F5F0] py-4 uppercase tracking-widest text-sm hover:bg-[#4A3F35] transition-colors">
                  Finalizar Compra
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* --- CABECERA (NAVBAR) --- */}
      <header className="px-8 py-6 flex flex-col md:flex-row justify-between items-center border-b border-[#2C241B]/10 bg-[#F7F5F0] sticky top-0 z-40 shadow-sm">
        <h1 className="text-4xl font-serif italic tracking-wide text-[#2C241B] mb-4 md:mb-0">Retro&Street</h1>
        <div className="flex items-center gap-8 text-sm uppercase tracking-widest font-medium">
          {usuario ? (
            <div className="flex items-center gap-4">
              <span>M. {usuario.nombre}</span>
              <button onClick={cerrarSesion} className="text-red-800/80 hover:text-red-800 hover:underline">Salir</button>
            </div>
          ) : (
            <button onClick={() => setMostrarAuth(true)} className="hover:text-[#8B7355] transition-colors">Entrar / Registro</button>
          )}
          <button onClick={() => setMostrarCarrito(true)} className="flex items-center gap-2 hover:text-[#8B7355] transition-colors">
            Cesta ({carrito.length})
          </button>
        </div>
      </header>

      {/* --- HERO BANNER --- */}
      <div className="py-20 text-center px-4 max-w-3xl mx-auto">
        <p className="uppercase tracking-[0.3em] text-[#8B7355] text-xs mb-4">Colección 2026</p>
        <h2 className="text-5xl md:text-6xl font-serif italic mb-6 text-[#2C241B]">Prendas con historia.</h2>
        <p className="text-stone-600 font-light leading-relaxed">Cada pieza ha sido cuidadosamente seleccionada para garantizar autenticidad y carácter. Descubre la elegancia del streetwear atemporal.</p>
      </div>

      {/* ---- GRID DE PRODUCTOS ---- */}
      {cargando ? (
        <div className="text-center py-20 font-serif text-xl italic text-stone-500 animate-pulse">Preparando el catálogo...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-x-8 gap-y-16 max-w-[90rem] mx-auto px-8">
          {articulos.map((art) => {
            const esFav = favoritos.includes(art.articulo_id);
            return (
              <div key={art.articulo_id} className="group cursor-pointer flex flex-col h-full">
                {/* Imagen */}
                <div className="relative aspect-[3/4] bg-[#EBE7E0] overflow-hidden mb-6">
                  <button onClick={() => toggleFavorito(art.articulo_id)} className="absolute top-4 right-4 z-10 text-2xl transition-transform hover:scale-110 opacity-0 group-hover:opacity-100">
                    {esFav ? '❤️' : '🤍'}
                  </button>
                  <img src={`http://localhost:8000${art.url_imagen}`} alt={art.nombre} className="w-full h-full object-cover mix-blend-multiply group-hover:scale-105 group-hover:sepia-[0.2] transition-all duration-700 ease-in-out" />
                  <span className="absolute bottom-0 left-0 bg-[#2C241B] text-[#F7F5F0] text-[10px] uppercase tracking-widest px-3 py-1 m-4">
                    {art.estado}
                  </span>
                </div>
                {/* Info */}
                <div className="flex flex-col flex-grow">
                  <h3 className="text-sm font-semibold uppercase tracking-wider mb-2 text-[#2C241B]">{art.nombre}</h3>
                  <div className="flex justify-between items-end mt-auto">
                    <span className="font-serif text-lg text-[#5C4A3D]">{art.precio_unitario}€</span>
                    <button onClick={() => añadirAlCarrito(art)} className="text-xs uppercase tracking-widest border-b border-[#2C241B] pb-0.5 hover:text-[#8B7355] hover:border-[#8B7355] transition-colors">
                      Añadir
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}


export default App;