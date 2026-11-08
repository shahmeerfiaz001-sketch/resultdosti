# Source reachability notes

Checked from GitHub Actions (US) and check-host.net nodes on 4-5 Nov 2026.

## Blocked outside India (disabled in sources.json)
- upsc.gov.in and its PDFs (/sites/default/files/...)
- RRB regional sites (rrbcdg, rrbmumbai, rrbpatna, rrbchennai, rrbkolkata, rrbajmer, rrbahmedabad, rrbsecunderabad, rrbmuzaffarpur, rrbguwahati, rrbbpl)
- rrb.indianrailways.gov.in (central RRB notices portal)
- joinindianarmy.nic.in, agnipathvayu.cdac.in, esic.gov.in
- rect.crpf.gov.in, cisfrectt.cisf.gov.in, recruitment.itbpolice.nic.in
- uppcl.org (403 outside India)
- epfindia.gov.in and rectt.bsf.gov.in (403 to data-centre IPs)

## Down from every region at test time
- upsssc.gov.in (timeouts everywhere, disabled), biharboardonline.bihar.gov.in (connection reset; use biharboardonline.com instead), upresults.nic.in, joinindiannavy.gov.in

## Reachable worldwide
- ssc.gov.in: public JSON API
  - /api/general-website/portal/notice-boards?page=1&limit=10&contentType=notice-boards&key=createdAt&order=DESC&isAttachment=true&language=english
  - /api/general-website/portal//lastUpdates
  - /api/general-website/portal/records?page=1&limit=10&contentType=browse-exam&key=createdAt&order=DESC&isPaginationRequired=false&isAttachment=true
- fci.gov.in: /admin/api/getWhatsNewDetails, /admin/api/ManageNewsPage/viewall
- opportunities.rbi.org.in/Scripts/Vacancies.aspx
- crpf.gov.in, www.cisf.gov.in (main sites)
- upsconline.nic.in (application portal only, no notice list)
- rrbapply.gov.in (single page app, root returns 404 before JS)
- indianrailways.gov.in

## Competitor clues
- sarkariresult.com.cm and sarkariresult.com link directly to upsc.gov.in and rrb.indianrailways.gov.in documents, so they collect from inside India.
- sarkariresult.com re-hosts official PDFs on doc.sarkariresults.org.in. ResultDosti only links to official sources.
