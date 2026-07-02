// Ruta del avatar por defecto
const AVATAR_DEFAULT = "uploads/avatares/no_avatar.png";

// Devuelve el HTML de un avatar. Si no tiene, usa no_avatar.png
function htmlAvatar(nombre, avatarRuta, claseExtra = "avatar-chico") {
    const ruta = avatarRuta || AVATAR_DEFAULT;
    return `<img src="/static/${ruta}" alt="${nombre || 'avatar'}" class="${claseExtra}">`;
}