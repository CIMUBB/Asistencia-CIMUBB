\LoadClass[a4paper,12pt]{article} % Clase de documento

%--------------------- Paquetes ------------------------
\RequirePackage[spanish]{babel}
\RequirePackage[utf8]{inputenc}
\RequirePackage[section]{placeins}
\RequirePackage[T1]{fontenc}
\RequirePackage{mlmodern}
\RequirePackage{mathtools}
\RequirePackage{siunitx}
\RequirePackage{float}
\RequirePackage{graphicx}
\RequirePackage[justification=centering]{caption}
\RequirePackage{subcaption}
\RequirePackage{wallpaper}
\RequirePackage{nomencl}
\RequirePackage[left=2.5cm,right=2.5cm,top=2cm,bottom=3.5cm]{geometry}
\RequirePackage{fancyhdr}
\RequirePackage{listings}
\RequirePackage{qrcode}
\RequirePackage{tikz}
\RequirePackage[none]{hyphenat}
\RequirePackage{tcolorbox}
\RequirePackage{amsmath}
\RequirePackage{amssymb}
\RequirePackage[hidelinks, breaklinks,  pdfusetitle]{hyperref}
\RequirePackage{url}
\RequirePackage{microtype}
\RequirePackage{enumitem}
\RequirePackage{soul}
\RequirePackage{overpic}
\RequirePackage{lipsum}

%---------------- Comandos personalizados ----------------------

\newcommand{\titulo}[1]{\renewcommand{\titulo}{#1}}
\newcommand{\integrantes}[1]{\renewcommand{\integrantes}{#1}}
\newcommand{\supervisor}[1]{\renewcommand{\supervisor}{#1}}
\newcommand{\carrera}[1]{\renewcommand{\carrera}{#1}}
\newcommand{\imagenlogoUNO}[1]{\renewcommand{\imagenlogoUNO}{#1}}
\newcommand{\imagenlogoDOS}[1]{\renewcommand{\imagenlogoDOS}{#1}}

\newcommand{\margenes}{
    \makenomenclature
    \pagestyle{fancy}
    \fancyheadoffset{1cm}
    \setlength{\headheight}{2cm}
    \lhead{\includegraphics[scale=0.3]{\imagenlogoDOS}}
    \rhead{\nouppercase{\leftmark}}
    \rfoot{\thepage}
    \cfoot{Informe - \textbf{\titulo}}
}



\newcommand{\portada}{
    \begin{titlepage}
    	\centering % Centralizar contenido
    	\includegraphics[scale=0.6]{\imagenlogoUNO} \par
        \vspace{1cm}
    	{
            \LARGE CIMUBB \\
            \small LABORATORIO DE SISTEMAS \\
            AUTOMATIZADOS DE PRODUCCION \\
            Facultad de Ingeniería \\
        } % Laboratorio
        \vspace{1cm}
    	{\scshape\Large \carrera \\ \vspace{1cm}} % Carrera
        \rule{\linewidth}{0.4 mm} \\[0.5 cm]
    	{\huge\bfseries \titulo \par} \ % Titulo
        \rule{\linewidth}{0.4 mm} \\[1.5 cm]
        
        \begin{minipage}[t]{0.45\textwidth}
            \raggedright
            \textit{\textbf{Integrantes :}}\\
            \integrantes
        \end{minipage}
        \hfill 
        \begin{minipage}[t]{0.45\textwidth}
            \raggedright
            \textit{\textbf{Supervisor :}}\\
            \supervisor
        \end{minipage}
    	\vfill
    	{\large \bf \today\par} % Fecha
    \end{titlepage}
}