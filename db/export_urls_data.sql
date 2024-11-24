SELECT id, key, secret_key, target_url,
	CASE 
		when is_active = 1 then 'true' 
		when is_active = 0 then 'false'
	end as is_active,
	clicks, created_at, updated_at, api_key,
	CASE 
		when is_checked = 1 then 'true' 
		when is_checked = 0 then 'false'
	end as is_checked,
	status, title, favicon_url
FROM urls;