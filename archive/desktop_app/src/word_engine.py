import os
from docxtpl import DocxTemplate

class WordEngine:
    def __init__(self):
        pass

    def procesar_reglas_gramaticales(self, variables: dict):
        """
        Aplica reglas gramaticales peruanas a las variables antes de inyectarlas.
        """
        def format_larga(fecha_str):
            fecha_str = str(fecha_str).strip()
            meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
            try:
                if '/' in fecha_str:
                    pd, pm, py = fecha_str.split('/')
                    return f"{pd} de {meses[int(pm) - 1]} de {py}"
            except:
                pass
            return fecha_str

        if 'FECHA_HOY_CORTA' in variables:
            variables['FECHA_HOY_LARGA'] = format_larga(variables['FECHA_HOY_CORTA'])

        for key in ('FECHA_CARTA', 'FECHA_INICIO', 'FECHA_FIN_CALCULADA'):
            if key in variables:
                variables[key] = format_larga(variables[key])

        distrito = str(variables.get('DISTRITO', '')).strip()
        if distrito.lower() == 'callao' or distrito.lower() == 'provincia constitucional del callao':
            variables['DE_DISTRITO'] = 'del Callao'
        else:
            variables['DE_DISTRITO'] = f"de {distrito}"

        planos_lista = variables.get('LISTA_PLANOS', [])
        if not planos_lista:
            variables['STRING_PLANOS'] = 'ninguno'
            return variables

        if len(planos_lista) == 1:
            variables['STRING_PLANOS'] = planos_lista[0]
            return variables

        ult_plano = str(planos_lista[-1]).strip()
        if ult_plano.lower().startswith('i') or ult_plano.lower().startswith('hi'):
            conector = ' e '
        else:
            conector = ' y '

        str_planos = ', '.join(planos_lista[:-1]) + conector + ult_plano
        variables['STRING_PLANOS'] = str_planos
        return variables

    def generar_documento(self, template_path: str, output_path: str, context_vars: dict) -> tuple[bool, str]:
        """
        Lee la plantilla docx, reemplaza etiquetas y guarda el resultado.
        """
        if not os.path.exists(template_path):
            return False, f"La plantilla '{template_path}' no existe o no fue encontrada."

        try:
            doc = DocxTemplate(template_path)
            context = self.procesar_reglas_gramaticales(context_vars)
            doc.render(context)
            doc.save(output_path)
            return True, f"Carta generada exitosamente en:\n{output_path}"
        except Exception as e:
            return False, f"Error al generar el documento Word:\n{str(e)}"
