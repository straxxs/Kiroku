const COLORS = {
    celeste: '#4FC3E8', celesteDark: '#1E9BC4',
    amarillo: '#FFCB3D', amarilloDark: '#F2A900',
    verde: '#4CB87D', verdeDark: '#2E9763',
    violeta: '#B39DDB', violetaDark: '#7E57C2',
    crema: '#FFFAF0', tinta: '#28344A',
};
const IC={'star':'<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>'};
function L(n,s){s=s||16;return `<svg class="luc" xmlns="http://www.w3.org/2000/svg" width="${s}" height="${s}" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${IC[n]}</svg>`}

function cargarEstadisticas() {
    fetch("/admin/stats")
        .then(res => res.json())
        .then(data => {
            if (!data.ok) {
                mostrarToast("Error al cargar estadísticas", "error");
                return;
            }

            // ---- Resumen general ----
            const g = data.generales;
            const grid = document.getElementById("statsGenerales");
            grid.className = "stats-grid";
            grid.innerHTML = `
                <div class="stat-box stat-celeste"><div class="stat-num">${g.total_usuarios}</div><div class="stat-label">Usuarios</div></div>
                <div class="stat-box stat-verde"><div class="stat-num">${g.usuarios_activos}</div><div class="stat-label">Activos</div></div>
                <div class="stat-box stat-rojo"><div class="stat-num">${g.usuarios_bloqueados}</div><div class="stat-label">Bloqueados</div></div>
                <div class="stat-box stat-amarillo"><div class="stat-num">${g.total_cursos}</div><div class="stat-label">Cursos</div></div>
                <div class="stat-box stat-celeste"><div class="stat-num">${g.total_materias}</div><div class="stat-label">Materias</div></div>
                <div class="stat-box stat-verde"><div class="stat-num">${g.apuntes_aprobados}</div><div class="stat-label">Apuntes aprobados</div></div>
                <div class="stat-box stat-amarillo"><div class="stat-num">${g.apuntes_pendientes}</div><div class="stat-label">Pendientes</div></div>
                <div class="stat-box stat-rojo"><div class="stat-num">${g.apuntes_rechazados}</div><div class="stat-label">Rechazados</div></div>
            `;

            // ---- Chart: Apuntes por estado ----
            const estadoLabels = data.por_estado.map(e => e.estado);
            const estadoData = data.por_estado.map(e => e.cantidad);
            const estadoColores = estadoLabels.map(e => {
                if (e === "aprobado") return COLORS.verde;
                if (e === "pendiente") return COLORS.amarillo;
                return COLORS.violeta;
            });
            new Chart(document.getElementById("chartEstado"), {
                type: "doughnut",
                data: {
                    labels: estadoLabels,
                    datasets: [{ data: estadoData, backgroundColor: estadoColores, borderWidth: 2 }]
                },
                options: { responsive: true, plugins: { legend: { position: "bottom" } } }
            });

            // ---- Chart: Apuntes por fecha ----
            const fechaLabels = data.por_fecha.map(f => f.fecha);
            const fechaData = data.por_fecha.map(f => f.cantidad);
            new Chart(document.getElementById("chartFecha"), {
                type: "line",
                data: {
                    labels: fechaLabels,
                    datasets: [{
                        label: "Apuntes subidos",
                        data: fechaData,
                        borderColor: COLORS.celeste,
                        backgroundColor: COLORS.celeste + "33",
                        fill: true,
                        tension: 0.3,
                    }]
                },
                options: { responsive: true, scales: { y: { beginAtZero: true } } }
            });

            // ---- Chart: Materias más consultadas ----
            const matLabels = data.materias_consultadas.map(m => m.materia);
            const matData = data.materias_consultadas.map(m => m.cantidad_apuntes);
            new Chart(document.getElementById("chartMaterias"), {
                type: "pie",
                data: {
                    labels: matLabels,
                    datasets: [{
                        data: matData,
                        backgroundColor: [COLORS.celeste, COLORS.amarillo, COLORS.verde, COLORS.violeta,
                            COLORS.celesteDark, COLORS.amarilloDark, COLORS.verdeDark],
                        borderWidth: 2,
                    }]
                },
                options: { responsive: true, plugins: { legend: { position: "bottom" } } }
            });

            // ---- Chart: Ranking de colaboradores ----
            const rankLabels = data.ranking.map(r => r.autor);
            const rankData = data.ranking.map(r => r.apuntes_subidos);
            new Chart(document.getElementById("chartRanking"), {
                type: "bar",
                data: {
                    labels: rankLabels,
                    datasets: [{
                        label: "Apuntes subidos",
                        data: rankData,
                        backgroundColor: COLORS.celesteDark,
                        borderRadius: 6,
                    }]
                },
                options: {
                    indexAxis: "y",
                    responsive: true,
                    scales: { x: { beginAtZero: true } },
                    plugins: { legend: { display: false } },
                }
            });

            // ---- Tabla: Apuntes más valorados ----
            const tabla = document.getElementById("tablaValorados");
            if (data.apuntes_valorados.length === 0) {
                tabla.innerHTML = '<p class="vacio">No hay apuntes con valoraciones aún.</p>';
            } else {
                let html = '<table><thead><tr><th>Título</th><th>Autor</th><th>Promedio</th><th>Cant.</th></tr></thead><tbody>';
                data.apuntes_valorados.forEach(a => {
                    html += `<tr><td>${escapeHtml(a.titulo || "(sin título)")}</td><td>${escapeHtml(a.autor || "-")}</td>
                        <td>${L("star",14)} ${a.promedio}</td><td>${a.cant_calificaciones}</td></tr>`;
                });
                html += '</tbody></table>';
                tabla.innerHTML = html;
            }
        })
        .catch(() => mostrarToast("Error de conexión", "error"));
}

cargarEstadisticas();
