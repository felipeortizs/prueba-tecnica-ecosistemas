/* QUERY INSUMO FINAL
 * 
 */
WITH CTE_APICALL AS (
	SELECT 
		date_api_call,
		commerce_id,
		ask_status,
		is_related
	FROM
		APICALL
),
CTE_COMMERCE AS (
	SELECT
		commerce_id,
		commerce_nit,
		commerce_name,
		commerce_status,
		commerce_email
	FROM
		COMMERCE
),
CTE_FINAL AS (
	SELECT
		AC.date_api_call, 
		AC.ask_status, 
		AC.is_related, 
		C.commerce_nit, 
		C.commerce_name, 
		C.commerce_status, 
		C.commerce_email
	FROM 
		CTE_APICALL AC
	LEFT JOIN
		CTE_COMMERCE C
		ON AC.commerce_id = C.commerce_id
	WHERE DATE_API_CALL BETWEEN '2024-07-01' AND '2024-09-01'
)--SELECT * FROM CTE_FINAL where commerce_nit = 445470636 ; 
, CTE_COMMISSION AS (
	SELECT 
		commerce_name,
		strftime('%Y-%m', date_api_call) AS month,
		COUNT(CASE WHEN ask_status = 'Successful' THEN 1 END) AS successful_requests,
		COUNT(CASE WHEN ask_status = 'Unsuccessful' THEN 1 END) AS unsuccessful_requests,
		CASE 
		-- Innovexa Solutions 
			WHEN commerce_nit = 445470636 THEN COUNT(CASE WHEN ask_status = 'Successful' THEN 1 END) * 300 
		-- QuantumLeap Inc 
			WHEN commerce_nit  = 198818316 THEN COUNT(CASE WHEN ask_status = 'Successful' THEN 1 END) * 600
		-- NexaTech Industries 
			WHEN commerce_nit = 452680670 THEN
				CASE 
				-- Por cada petición exitosa a la API de entre 0 – 10.000 peticiones totales al mes, cobrarán $250 pesos colombianos más IVA.
					WHEN COUNT(CASE WHEN ask_status = 'Successful' THEN 1 END) BETWEEN 0 AND 10000 THEN COUNT(CASE WHEN ask_status = 'Successful' THEN 1 END) * 250
				-- Por cada petición exitosa a la API de entre 10.001 – 20.000 peticiones totales al mes, cobrarán $200 pesos colombianos más IVA.
					WHEN COUNT(CASE WHEN ask_status = 'Successful' THEN 1 END) BETWEEN 10001 AND 20000 THEN COUNT(CASE WHEN ask_status = 'Successful' THEN 1 END) * 200
				-- Por cada petición exitosa a la API de más de 20.001 peticiones totales al mes, cobrarán $170 pesos colombianos más IVA.
					WHEN COUNT(CASE WHEN ask_status = 'Successful' THEN 1 END) > 20001 THEN COUNT(CASE WHEN ask_status = 'Successful' THEN 1 END) * 170
				END
		-- Zenith Corp 
			WHEN commerce_nit = 28960112 THEN
				CASE 
				-- Por cada petición exitosa a la API de entre 0 – 22.000 peticiones totales al mes, cobrarán $250 pesos colombianos más IVA.
					WHEN COUNT(CASE WHEN ask_status = 'Successful' THEN 1 END) BETWEEN 0 AND 22000 THEN COUNT(CASE WHEN ask_status = 'Successful' THEN 1 END) * 250
				-- Por cada petición exitosa a la API de más de 22.001 peticiones totales al mes, cobrarán $130 pesos colombianos más IVA.
					WHEN COUNT(CASE WHEN ask_status = 'Successful' THEN 1 END) > 22001 THEN COUNT(CASE WHEN ask_status = 'Successful' THEN 1 END) * 130
				END
				- CASE 
				-- Adicional si, la entidad tiene más de 6.000 peticiones no exitosas totales al mes a la API, se le descontará el 5% del valor total facturado al mes afectado antes de IVA
					WHEN COUNT(CASE WHEN ask_status = 'Unsuccessful' THEN 1 END) > 6000 THEN (COUNT(CASE WHEN ask_status = 'Successful' THEN 1 END) * 0.05)
					ELSE 0 
				END
		-- FusionWave Enterprises 
			WHEN commerce_nit = 919341007 THEN
				COUNT(CASE WHEN ask_status = 'Successful' THEN 1 END) * 300 
				- CASE 
				-- Si tiene entre 2.500 a 4.500 peticiones no exitosas totales al mes a la API, se le descontará el 5% del valor total facturado al mes afectado antes de IVA.
					WHEN COUNT(CASE WHEN ask_status = 'Unsuccessful' THEN 1 END) BETWEEN 2500 AND 4500 THEN (COUNT(CASE WHEN ask_status = 'Successful' THEN 1 END) * 0.05)
				-- Si tiene más de 4.501 peticiones no exitosas totales al mes a la API, se le descontará el 8% del valor total facturado al mes afectado antes de IVA.
					WHEN COUNT(CASE WHEN ask_status = 'Unsuccessful' THEN 1 END) > 4501 THEN (COUNT(CASE WHEN ask_status = 'Successful' THEN 1 END) * 0.08)
					ELSE 0
				END
		END AS commission_amount
		,commerce_email
		, COMMERCE_NIT
	FROM 
		CTE_FINAL
	WHERE
		commerce_status = 'Active'
		AND DATE_API_CALL BETWEEN '2024-07-01' AND '2024-09-01'
	GROUP BY
		commerce_name, month
)--SELECT * FROM CTE_COMMISSION;
SELECT 
	month FECHA_MES,
	commerce_name NOMBRE, 
	COMMERCE_NIT NIT,
	commission_amount VALOR_COMISION,
	commission_amount * 0.19 AS VALOR_IVA,
	commission_amount + (commission_amount * 0.19) AS VALOR_TOTAL,
	commerce_email CORREO
FROM 
	CTE_COMMISSION
ORDER BY 
	commerce_name, month;