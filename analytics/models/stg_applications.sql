select application_id, application_date::date as application_date,
       amount_eur::decimal(12,2) as amount_eur,
       income_eur::decimal(12,2) as income_eur,
       term_months::integer as term_months, status, channel
from {{ ref('applications') }}
