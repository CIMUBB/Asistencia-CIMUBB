CREATE TABLE Usuario (
    rut VARCHAR(10) PRIMARY KEY NOT NULL,
    nombre_completo VARCHAR(50) DEFAULT '',
    email VARCHAR(50) DEFAULT '',
    tipo_usuario VARCHAR(15) NOT NULL,
    foto_perfil BYTEA DEFAULT NULL
);

CREATE TABLE Registro (
    id_registro VARCHAR(10) PRIMARY KEY NOT NULL,
    fecha DATE NOT NULL,
    hora_ingreso TIME NOT NULL,
    hora_salida TIME DEFAULT NULL,
    motivo VARCHAR(50) NOT NULL,
    rut VARCHAR(10) NOT NULL,
    FOREIGN KEY (rut) REFERENCES Usuario(rut)
);

CREATE TABLE Login (
    id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    password VARCHAR NOT NULL
);

-- Asegurar que estamos en la base de datos correcta
\c cimubb_asistencia;

-- Extensión para almacenar contraseñas encriptadas
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Insertar usuario administrador con contraseña encriptada
INSERT INTO Login (username, password)
VALUES ('admin', crypt('admin', gen_salt('bf')));

-- Ejempplo
-- INSERT INTO Usuario (rut, nombre_completo, email, tipo_usuario, foto_perfil)
-- VALUES ('12345678-9', 'Usuario1', 'usuario@ejemplo.com', 'Estudiante', NULL)
-- ON CONFLICT (rut) DO NOTHING;

-- INSERT INTO Registro (id_registro, fecha, hora_ingreso, hora_salida, motivo, rut)
-- VALUES ('R001', CURRENT_DATE, '08:00:00', NULL, 'Ingreso matutino', '12345678-9')
-- ON CONFLICT (id_registro) DO NOTHING;

-- Habilitar pg_cron si no existe
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Crear la función para actualizar la hora de salida automáticamente
CREATE OR REPLACE FUNCTION marcar_salida_automatica()
RETURNS VOID AS $$
BEGIN
    UPDATE Registro
    SET hora_salida = '19:00:00'
    WHERE hora_salida IS NULL AND fecha = CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;

-- Programar la tarea para ejecutarse todos los días a las HH:MM
SELECT cron.schedule(
    'marcar_salida_diaria',
    '00 22 * * *',  -- MM HH DD MM DOW (https://crontab.guru/)
    'SELECT marcar_salida_automatica();'
);

CREATE OR REPLACE FUNCTION actualizar_horario_pgcron()
RETURNS VOID AS $$
DECLARE
    diferencia_horaria INT;
    nueva_hora INT;
    nueva_hora_cron INT;
BEGIN
    -- Detectar la diferencia horaria real de Chile con UTC
    SELECT EXTRACT(TIMEZONE_HOUR FROM NOW() AT TIME ZONE 'America/Santiago') INTO diferencia_horaria;

    IF diferencia_horaria = -3 THEN
        nueva_hora := 22;  -- Chile UTC-3 (verano)
        nueva_hora_cron := 3; -- Medianoche en Chile en UTC-3
    ELSE
        nueva_hora := 23;  -- Chile UTC-4 (invierno)
        nueva_hora_cron := 4; -- Medianoche en Chile en UTC-4
    END IF;

    -- Eliminar el job anterior si existe
    PERFORM cron.unschedule('marcar_salida_diaria');
    PERFORM cron.unschedule('actualizar_horario_diario');

    -- Programar la tarea para actualizar la salida automática
    PERFORM cron.schedule(
        'marcar_salida_diaria',
        format('00 %s * * *', nueva_hora),
        'SELECT marcar_salida_automatica();'
    );

    -- Programar la tarea para actualizar el horario de ejecución
    PERFORM cron.schedule(
        'actualizar_horario_diario',
        format('0 %s * * *', nueva_hora_cron),
        'SELECT actualizar_horario_pgcron();'
    );
END;
$$ LANGUAGE plpgsql;


SELECT cron.schedule(
    'actualizar_horario_diario',
    '0 3 * * *',  -- Ejecutar cada día a medianoche UTC CHILE
    'SELECT actualizar_horario_pgcron();'
);

CREATE OR REPLACE FUNCTION notify_registro_changes()
RETURNS TRIGGER AS $$
DECLARE
    payload TEXT;
BEGIN
    IF TG_OP = 'INSERT' THEN
        payload := NEW.rut || ' ingreso a las ' || TO_CHAR(NEW.hora_ingreso, 'HH24:MI');
    ELSIF TG_OP = 'UPDATE' AND OLD.hora_salida IS DISTINCT FROM NEW.hora_salida THEN
        payload := NEW.rut || ' salio a las ' || TO_CHAR(NEW.hora_salida, 'HH24:MI');
    ELSE
        RETURN NEW;
    END IF;

    PERFORM pg_notify('notify_channel', payload);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE TRIGGER registro_notify_trigger
AFTER INSERT OR UPDATE ON Registro
FOR EACH ROW
EXECUTE FUNCTION notify_registro_changes();