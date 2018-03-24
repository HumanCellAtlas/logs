aws logs put-subscription-filter \
	--log-group-name "${1}" \
	--filter-name firehose \
	--filter-pattern "" \
	--destination-arn "${2}" \
	--role-arn "${3}"
