select application_date, channel, count(*) as applications,
       sum(case when status = 'approved' then 1 else 0 end) as approved,
       sum(case when status = 'approved' then amount_eur else 0 end) as approved_volume_eur,
       avg(amount_eur) as average_requested_eur
from {{ ref('stg_applications') }}
group by application_date, channel
