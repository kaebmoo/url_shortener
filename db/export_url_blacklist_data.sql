SELECT id, url, category, date_added, reason, 
	CASE 
		when status = 1 then 'true'
		when status = 0 then 'false'
	END as status,
	"source"
FROM url;