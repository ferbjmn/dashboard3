import streamlit as st
import pandas as pd
import yfinance as yf
import time  # Importamos time para la pausa

def redondear_y_formatear(valor, es_porcentaje=False):
    """Redondear los valores y formatearlos como porcentaje si es necesario"""
    try:
        # Verificar si el valor es nulo o no es un número
        if valor is None or valor == "N/D":
            return "N/D"
        
        # Si es porcentaje, lo convertimos en formato porcentaje
        if es_porcentaje:
            if isinstance(valor, (int, float)):  # Verificamos que el valor sea numérico
                return f"{round(valor * 100, 2):.2f}%"  # Formato porcentaje
            else:
                return "N/D"  # Si no es numérico, devolvemos "N/D"
        else:
            # Redondeo para valores decimales
            return round(valor, 2) if isinstance(valor, (int, float)) else "N/D"
    except Exception as e:
        return "N/D"

def calcular_wacc_y_roic(ticker):
    """
    Calcula el WACC y el ROIC de una empresa usando únicamente datos de yfinance,
    e incluye una evaluación de si la empresa está creando valor (Relación ROIC-WACC).
    """
    try:
        empresa = yf.Ticker(ticker)
        
        # Información básica
        market_cap = empresa.info.get('marketCap', 0)  # Capitalización de mercado (valor de mercado del patrimonio)
        beta = empresa.info.get('beta', 1)  # Beta de la empresa
        rf = 0.02  # Tasa libre de riesgo (asumida como 2%)
        equity_risk_premium = 0.05  # Prima de riesgo del mercado (asumida como 5%)
        ke = rf + beta * equity_risk_premium  # Costo del capital accionario (CAPM)
        
        balance_general = empresa.balance_sheet
        deuda_total = balance_general.loc['Total Debt'].iloc[0] if 'Total Debt' in balance_general.index else 0
        efectivo = balance_general.loc['Cash And Cash Equivalents'].iloc[0] if 'Cash And Cash Equivalents' in balance_general.index else 0
        patrimonio = balance_general.loc['Common Stock Equity'].iloc[0] if 'Common Stock Equity' in balance_general.index else 0
        
        estado_resultados = empresa.financials
        gastos_intereses = estado_resultados.loc['Interest Expense'].iloc[0] if 'Interest Expense' in estado_resultados.index else 0
        ebt = estado_resultados.loc['Ebt'].iloc[0] if 'Ebt' in estado_resultados.index else 0
        impuestos = estado_resultados.loc['Income Tax Expense'].iloc[0] if 'Income Tax Expense' in estado_resultados.index else 0
        ebit = estado_resultados.loc['EBIT'].iloc[0] if 'EBIT' in estado_resultados.index else 0

        # Calcular Kd (costo de la deuda)
        kd = gastos_intereses / deuda_total if deuda_total != 0 else 0

        # Calcular tasa de impuestos efectiva
        tasa_impuestos = impuestos / ebt if ebt != 0 else 0.21  # Asume 21% si no hay datos
        
        # Calcular WACC
        total_capital = market_cap + deuda_total
        wacc = ((market_cap / total_capital) * ke) + ((deuda_total / total_capital) * kd * (1 - tasa_impuestos))
        
        # Calcular ROIC
        nopat = ebit * (1 - tasa_impuestos)  # NOPAT
        capital_invertido = patrimonio + (deuda_total - efectivo)  # Capital Invertido
        roic = nopat / capital_invertido if capital_invertido != 0 else 0
        
        # Calcular Relación ROIC-WACC
        diferencia_roic_wacc = roic - wacc
        creando_valor = roic > wacc  # Determina si está creando valor

        # Mostrar resultados
        return wacc, roic, creando_valor
    except Exception as e:
        st.error(f"Error al calcular WACC y ROIC para {ticker.upper()}: {e}")
        return None, None, None

def obtener_datos_financieros(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        bs = stock.balance_sheet
        fin = stock.financials
        cf = stock.cashflow

        # Datos básicos
        price = info.get("currentPrice")
        name = info.get("longName", ticker)
        sector = info.get("sector", "N/D")
        country = info.get("country", "N/D")
        industry = info.get("industry", "N/D")

        # Ratios de valoración
        pe = info.get("trailingPE")
        pb = info.get("priceToBook")
        dividend = info.get("dividendRate")
        payout = info.get("payoutRatio")
        
        # Dividend Est. en formato de número
        dividend_est = dividend if dividend else 0  # Si no está disponible, asignamos 0

        # Ratios de rentabilidad
        roa = info.get("returnOnAssets")
        roe = info.get("returnOnEquity")
        
        # Ratios de liquidez
        current_ratio = info.get("currentRatio")
        quick_ratio = info.get("quickRatio")
        
        # Margenes
        op_margin = info.get("operatingMargins")
        profit_margin = info.get("profitMargins")
        
        # Flujo de caja
        fcf = cf.loc["Free Cash Flow"].iloc[0] if "Free Cash Flow" in cf.index else None
        shares = info.get("sharesOutstanding")
        pfcf = price / (fcf / shares) if fcf and shares else None
        
        # Cálculos avanzados: WACC y ROIC
        wacc, roic, creando_valor = calcular_wacc_y_roic(ticker)
        
        # Crecimientos
        revenue_growth = calcular_crecimiento_historico(fin, "Total Revenue")
        eps_growth = calcular_crecimiento_historico(fin, "Net Income")
        fcf_growth = calcular_crecimiento_historico(cf, "Free Cash Flow") or calcular_crecimiento_historico(cf, "Operating Cash Flow")
        
        # Liquidez avanzada
        cash_ratio = info.get("cashRatio")
        operating_cash_flow = cf.loc["Operating Cash Flow"].iloc[0] if "Operating Cash Flow" in cf.index else None
        current_liabilities = bs.loc["Total Current Liabilities"].iloc[0] if "Total Current Liabilities" in bs.index else None
        cash_flow_ratio = operating_cash_flow / current_liabilities if operating_cash_flow and current_liabilities else None
        
        # Redondear los valores numéricos a dos decimales
        return {
            "Ticker": ticker,
            "Nombre": name,
            "Sector": sector,
            "País": country,
            "Industria": industry,
            "Precio": redondear_y_formatear(price),
            "P/E": redondear_y_formatear(pe),
            "P/B": redondear_y_formatear(pb),
            "P/FCF": redondear_y_formatear(pfcf),
            "Dividend Est.": redondear_y_formatear(dividend_est),
            "Payout Ratio": redondear_y_formatear(payout, True),  # Formato porcentaje
            "ROA": redondear_y_formatear(roa, True),
            "ROE": redondear_y_formatear(roe, True),
            "Current Ratio": redondear_y_formatear(current_ratio),
            "Quick Ratio": redondear_y_formatear(quick_ratio),
            "LtDebt/Eq": redondear_y_formatear(ltde),
            "Debt/Eq": redondear_y_formatear(de),
            "Oper Margin": redondear_y_formatear(op_margin, True),
            "Profit Margin": redondear_y_formatear(profit_margin, True),
            "WACC": redondear_y_formatear(wacc, True),
            "ROIC": redondear_y_formatear(roic, True),  # Ajuste para ROIC
            "EVA": redondear_y_formatear("N/D" if not creando_valor else "Creando Valor"),  # EVA dependerá de ROIC
            "Deuda Total": redondear_y_formatear(total_debt),
            "Patrimonio Neto": redondear_y_formatear(patrimonio),
            "Revenue Growth": redondear_y_formatear(revenue_growth, True),
            "EPS Growth": redondear_y_formatear(eps_growth, True),
            "FCF Growth": redondear_y_formatear(fcf_growth, True),
            "Cash Ratio": redondear_y_formatear(cash_ratio),
            "Cash Flow Ratio": redondear_y_formatear(cash_flow_ratio),
            "Operating Cash Flow": redondear_y_formatear(operating_cash_flow),
            "Current Liabilities": redondear_y_formatear(current_liabilities),
        }
    except Exception as e:
        return {"Ticker": ticker, "Error": str(e)}

# Interfaz de usuario
def main():
    st.title("📊 Dashboard de Análisis Financiero Avanzado")
    
    # Sidebar con configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        tickers_input = st.text_area(
            "🔎 Ingresa tickers (separados por coma)", 
            "AAPL, MSFT, GOOGL, AMZN, TSLA",
            help="Ejemplo: AAPL, MSFT, GOOG"
        )
        max_tickers = st.slider("Número máximo de tickers", 1, 50, 10)
        
        st.markdown("---")
        st.markdown("**Parámetros WACC**")
        global Rf, Rm, Tc
        Rf = st.number_input("Tasa libre de riesgo (%)", min_value=0.0, max_value=20.0, value=4.35) / 100
        Rm = st.number_input("Retorno esperado del mercado (%)", min_value=0.0, max_value=30.0, value=8.5) / 100
        Tc = st.number_input("Tasa impositiva corporativa (%)", min_value=0.0, max_value=50.0, value=21.0) / 100
    
    # Procesamiento de tickers
    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()][:max_tickers]
    
    if st.button("🔍 Analizar Acciones", type="primary"):
        if not tickers:
            st.warning("Por favor ingresa al menos un ticker")
            return
            
        resultados = {}
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Ciclo de procesamiento de tickers
        for i, t in enumerate(tickers):
            status_text.text(f"⏳ Procesando {t} ({i+1}/{len(tickers)})...")
            resultados[t] = obtener_datos_financieros(t)
            progress_bar.progress((i + 1) / len(tickers))
            
            # Pausa de 1 segundo entre cada solicitud para evitar bloqueo
            time.sleep(1)  # Evita bloqueo por demasiadas consultas
        
        status_text.text("✅ Análisis completado!")
        status_text.empty()
        progress_bar.empty()
        
        # Mostrar resultados
        if resultados:
            datos = list(resultados.values())
            
            # Filtramos empresas con errores
            datos_validos = [d for d in datos if "Error" not in d]
            if not datos_validos:
                st.error("No se pudo obtener datos válidos para ningún ticker")
                return
                
            df = pd.DataFrame(datos_validos)
            
            # Sección 1: Resumen General
            st.header("📋 Resumen General")
            
            # Formatear columnas porcentuales
            porcentajes = ["Dividend Est.", "Payout Ratio", "ROA", "ROE", "Oper Margin", "Profit Margin", "WACC", "ROIC", "EVA"]
            for col in porcentajes:
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: redondear_y_formatear(x, True) if pd.notnull(x) else "N/D")
    
            # Definir el orden de las columnas
            columnas_mostrar = [
                "Ticker", "Nombre", "Sector", "Precio", "P/E", "P/B", "P/FCF", 
                "Dividend Est.", "Payout Ratio", "ROA", "ROE", "Current Ratio", 
                "Quick Ratio", "LtDebt/Eq", "Debt/Eq", "Oper Margin", "Profit Margin", 
                "WACC", "ROIC", "EVA"
            ]
    
            # Mostrar el dataframe con las columnas en el orden adecuado
            st.dataframe(
                df[columnas_mostrar].dropna(how='all', axis=1),
                use_container_width=True,
                height=400
            )
            
            # Sección 2: Análisis de Valoración
            st.header("💰 Análisis de Valoración")
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Ratios de Valoración")
                fig, ax = plt.subplots(figsize=(10, 4))
                df_plot = df[["Ticker", "P/E", "P/B", "P/FCF"]].set_index("Ticker").apply(pd.to_numeric, errors='coerce')
                df_plot.plot(kind="bar", ax=ax, rot=45)
                ax.set_title("Comparativa de Ratios de Valoración")
                ax.set_ylabel("Ratio")
                st.pyplot(fig)
                plt.close()
                
            with col2:
                st.subheader("Dividendos")
                fig, ax = plt.subplots(figsize=(10, 4))
                df_plot = df[["Ticker", "Dividend Est."]].set_index("Ticker")
                df_plot["Dividend Est."] = df_plot["Dividend Est."].replace("N/D", 0)
                df_plot["Dividend Est."] = df_plot["Dividend Est."].astype("float")
                df_plot.plot(kind="bar", ax=ax, rot=45, color="green")
                ax.set_title("Rendimiento de Dividendos Estimados")
                ax.set_ylabel("Dividend Est.")
                st.pyplot(fig)
                plt.close()
            
            # Sección 3: Rentabilidad y Eficiencia
            st.header("📈 Rentabilidad y Eficiencia")
            
            tabs = st.tabs(["ROE vs ROA", "Margenes", "WACC vs ROIC"])
            
            with tabs[0]:
                fig, ax = plt.subplots(figsize=(10, 5))
                df_plot = df[["Ticker", "ROE", "ROA"]].set_index("Ticker")
                df_plot["ROE"] = df_plot["ROE"].str.rstrip("%").astype("float")
                df_plot["ROA"] = df_plot["ROA"].str.rstrip("%").astype("float")
                df_plot.plot(kind="bar", ax=ax, rot=45)
                ax.set_title("ROE vs ROA (%)")
                ax.set_ylabel("Porcentaje")
                st.pyplot(fig)
                plt.close()
                
            with tabs[1]:
                fig, ax = plt.subplots(figsize=(10, 5))
                df_plot = df[["Ticker", "Oper Margin", "Profit Margin"]].set_index("Ticker")
                df_plot["Oper Margin"] = df_plot["Oper Margin"].str.rstrip("%").astype("float")
                df_plot["Profit Margin"] = df_plot["Profit Margin"].str.rstrip("%").astype("float")
                df_plot.plot(kind="bar", ax=ax, rot=45)
                ax.set_title("Margen Operativo vs Margen Neto (%)")
                ax.set_ylabel("Porcentaje")
                st.pyplot(fig)
                plt.close()
                
            with tabs[2]:
                fig, ax = plt.subplots(figsize=(10, 5))
                for _, row in df.iterrows():
                    wacc = float(row["WACC"].rstrip("%")) if row["WACC"] != "N/D" else None
                    roic = float(row["ROIC"].rstrip("%")) if row["ROIC"] != "N/D" else None
                    
                    if wacc and roic:
                        color = "green" if roic > wacc else "red"
                        ax.bar(row["Ticker"], roic, color=color, alpha=0.6, label="ROIC")
                        ax.bar(row["Ticker"], wacc, color="gray", alpha=0.3, label="WACC")
                
                ax.set_title("Creación de Valor: ROIC vs WACC (%)")
                ax.set_ylabel("Porcentaje")
                ax.legend()
                st.pyplot(fig)
                plt.close()
            
            # Sección 4: Análisis de Deuda
            st.header("🏦 Estructura de Capital y Deuda")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Apalancamiento")
                fig, ax = plt.subplots(figsize=(10, 5))
                df_plot = df[["Ticker", "Debt/Eq", "LtDebt/Eq"]].set_index("Ticker")
                df_plot = df_plot.apply(pd.to_numeric, errors='coerce')
                df_plot.plot(kind="bar", stacked=True, ax=ax, rot=45)
                ax.axhline(1, color="red", linestyle="--")
                ax.set_title("Deuda/Patrimonio")
                ax.set_ylabel("Ratio")
                st.pyplot(fig)
                plt.close()
                
            with col2:
                st.subheader("Liquidez")
                fig, ax = plt.subplots(figsize=(10, 5))
                df_plot = df[["Ticker", "Current Ratio", "Quick Ratio", "Cash Ratio"]].set_index("Ticker")
                df_plot = df_plot.apply(pd.to_numeric, errors='coerce')
                df_plot.plot(kind="bar", ax=ax, rot=45)
                ax.axhline(1, color="green", linestyle="--")
                ax.set_title("Ratios de Liquidez")
                ax.set_ylabel("Ratio")
                st.pyplot(fig)
                plt.close()
            
            # Sección 5: Crecimiento
            st.header("🚀 Crecimiento Histórico")
            
            growth_metrics = ["Revenue Growth", "EPS Growth", "FCF Growth"]
            df_growth = df[["Ticker"] + growth_metrics].set_index("Ticker")
            df_growth = df_growth * 100  # Convertir a porcentaje
            
            fig, ax = plt.subplots(figsize=(12, 6))
            df_growth.plot(kind="bar", ax=ax, rot=45)
            ax.axhline(0, color="black", linewidth=0.8)
            ax.set_title("Tasas de Crecimiento Anual (%)")
            ax.set_ylabel("Crecimiento %")
            st.pyplot(fig)
            plt.close()
            
            # Sección 6: Análisis Individual
            st.header("🔍 Análisis por Empresa")
            
            selected_ticker = st.selectbox("Selecciona una empresa", df["Ticker"].unique())
            empresa = df[df["Ticker"] == selected_ticker].iloc[0]
            
            st.subheader(f"Análisis Detallado: {empresa['Nombre']}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Precio", f"${empresa['Precio']:,.2f}" if empresa['Precio'] else "N/D")
                st.metric("P/E", empresa['P/E'])
                st.metric("P/B", empresa['P/B'])
                
            with col2:
                st.metric("ROE", empresa['ROE'])
                st.metric("ROIC", empresa['ROIC'])
                st.metric("WACC", empresa['WACC'])
                
            with col3:
                st.metric("Deuda/Patrimonio", empresa['Debt/Eq'])
                st.metric("Margen Neto", empresa['Profit Margin'])
                st.metric("Dividend Est.", empresa['Dividend Est.'])
            
            # Gráfico de creación de valor individual
            st.subheader("Creación de Valor")
            fig, ax = plt.subplots(figsize=(6, 4))
            if empresa['ROIC'] != "N/D" and empresa['WACC'] != "N/D":
                roic_val = float(empresa['ROIC'].rstrip("%"))
                wacc_val = float(empresa['WACC'].rstrip("%"))
                color = "green" if roic_val > wacc_val else "red"
                
                ax.bar(["ROIC", "WACC"], [roic_val, wacc_val], color=[color, "gray"])
                ax.set_title("Creación de Valor (ROIC vs WACC)")
                ax.set_ylabel("%")
                st.pyplot(fig)
                plt.close()
                
                if roic_val > wacc_val:
                    st.success("✅ La empresa está creando valor (ROIC > WACC)")
                else:
                    st.error("❌ La empresa está destruyendo valor (ROIC < WACC)")
            else:
                st.warning("Datos insuficientes para análisis ROIC/WACC")

if __name__ == "__main__":
    main()
