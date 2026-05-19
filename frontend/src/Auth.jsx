import { useState } from 'react';

export default function Auth({ onLogin, onCerrar }) {
  const [esRegistro, setEsRegistro] = useState(false);
  const [formData, setFormData] = useState({ nombre: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [cargando, setCargando] = useState(false);

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setCargando(true);
    const endpoint = esRegistro ? 'register' : 'login';
    
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(
          esRegistro 
            ? { nombre: formData.nombre, apellidos: "", email: formData.email, telefono: "", direccion: "", password: formData.password }
            : { email: formData.email, password: formData.password }
        )
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Ocurrió un error');
      
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('usuario', JSON.stringify(data.usuario));
      onLogin(data.usuario);
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-[#2C241B]/60 backdrop-blur-md flex justify-center items-center z-50 p-4 transition-opacity">
      <div className="bg-[#F7F5F0] p-10 max-w-sm w-full relative shadow-2xl">
        <button onClick={onCerrar} className="absolute top-4 right-4 text-stone-400 hover:text-[#2C241B] transition-colors text-xl">✕</button>
        <h2 className="text-3xl font-serif italic text-center text-[#2C241B] mb-8">
          {esRegistro ? 'Crear Cuenta' : 'Bienvenido'}
        </h2>

        {error && <div className="text-red-800 text-sm text-center mb-6 bg-red-100 py-2">{error}</div>}

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          {esRegistro && (
            <input type="text" name="nombre" placeholder="Nombre completo" required onChange={handleChange} value={formData.nombre}
              className="bg-transparent border-b border-[#2C241B]/30 pb-2 text-sm outline-none focus:border-[#2C241B] transition-colors placeholder:text-stone-400" />
          )}
          <input type="email" name="email" placeholder="Correo electrónico" required onChange={handleChange} value={formData.email}
            className="bg-transparent border-b border-[#2C241B]/30 pb-2 text-sm outline-none focus:border-[#2C241B] transition-colors placeholder:text-stone-400" />
          <input type="password" name="password" placeholder="Contraseña" required onChange={handleChange} value={formData.password}
            className="bg-transparent border-b border-[#2C241B]/30 pb-2 text-sm outline-none focus:border-[#2C241B] transition-colors placeholder:text-stone-400" />
          
          <button type="submit" disabled={cargando} className="bg-[#2C241B] text-[#F7F5F0] py-4 mt-4 uppercase tracking-widest text-xs hover:bg-[#4A3F35] disabled:bg-stone-300 transition-colors">
            {cargando ? 'Procesando...' : (esRegistro ? 'Registrarse' : 'Acceder')}
          </button>
        </form>

        <p className="mt-8 text-center text-xs text-stone-500 uppercase tracking-widest">
          {esRegistro ? '¿Ya tiene cuenta?' : '¿Cliente nuevo?'}
          <button onClick={() => { setEsRegistro(!esRegistro); setError(''); }} className="ml-2 text-[#2C241B] border-b border-[#2C241B] hover:text-[#8B7355] hover:border-[#8B7355] transition-colors pb-0.5">
            {esRegistro ? 'Iniciar sesión' : 'Registrarse'}
          </button>
        </p>
      </div>
    </div>
  );
}