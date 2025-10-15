"""Stage 6: Report Generation - Create HTML email report with findings."""

import logging
from datetime import datetime

from agents.models import Opportunity

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates HTML email reports from daily research results."""

    def generate_report(
        self,
        opportunities: list[Opportunity],
        run_date: datetime,
        runtime_seconds: float,
        estimated_cost: float,
        errors: list[str] = None,
    ) -> str:
        """
        Generate HTML email report.

        Args:
            opportunities: List of identified opportunities.
            run_date: Date of the analysis run.
            runtime_seconds: Total runtime in seconds.
            estimated_cost: Estimated API cost.
            errors: List of errors encountered.

        Returns:
            HTML string for email body.
        """
        logger.info(f"Generating report with {len(opportunities)} opportunities")

        # Categorize opportunities
        high_priority = [o for o in opportunities if o.opportunity_score >= 0.10]
        medium_priority = [
            o for o in opportunities if 0.05 <= o.opportunity_score < 0.10
        ]

        # Generate HTML sections
        html = self._html_header()
        html += self._html_executive_summary(
            run_date, len(opportunities), high_priority, runtime_seconds, estimated_cost
        )

        if high_priority:
            html += self._html_high_priority_section(high_priority)

        if medium_priority:
            html += self._html_medium_priority_section(medium_priority)

        if errors:
            html += self._html_errors_section(errors)

        html += self._html_footer(run_date, runtime_seconds)

        return html

    def _html_header(self) -> str:
        """Generate HTML header with email-compatible styles."""
        return """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Polymarket Trading Opportunities</title>
    <!--[if mso]>
    <noscript>
        <xml>
            <o:OfficeDocumentSettings>
                <o:PixelsPerInch>96</o:PixelsPerInch>
            </o:OfficeDocumentSettings>
        </xml>
    </noscript>
    <![endif]-->
    <style type="text/css">
        /* Reset styles */
        body, table, td, p, a, li, blockquote {
            -webkit-text-size-adjust: 100%;
            -ms-text-size-adjust: 100%;
        }
        table, td {
            mso-table-lspace: 0pt;
            mso-table-rspace: 0pt;
        }
        img {
            -ms-interpolation-mode: bicubic;
        }
        
        /* Main styles */
        body {
            margin: 0 !important;
            padding: 0 !important;
            background-color: #f5f5f5;
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333333;
        }
        
        .email-container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
        }
        
        .content {
            padding: 30px;
        }
        
        h1 {
            color: #2c3e50;
            font-size: 24px;
            font-weight: bold;
            margin: 0 0 20px 0;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        
        h2 {
            color: #34495e;
            font-size: 20px;
            font-weight: bold;
            margin: 30px 0 15px 0;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
        }
        
        h3 {
            color: #7f8c8d;
            font-size: 16px;
            font-weight: bold;
            margin: 20px 0 10px 0;
        }
        
        .summary-box {
            background-color: #ecf0f1;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 20px 0;
        }
        
        .opportunity {
            background-color: #f8f9fa;
            border-left: 4px solid #27ae60;
            padding: 20px;
            margin: 20px 0;
        }
        
        .opportunity.medium {
            border-left-color: #f39c12;
        }
        
        .metric {
            display: inline-block;
            background-color: #3498db;
            color: #ffffff;
            padding: 5px 10px;
            margin: 5px 5px 5px 0;
            font-size: 12px;
            font-weight: bold;
        }
        
        .metric.edge {
            background-color: #27ae60;
        }
        
        .metric.score {
            background-color: #e74c3c;
        }
        
        .metric.confidence {
            background-color: #9b59b6;
        }
        
        .flag {
            display: inline-block;
            padding: 3px 8px;
            margin: 3px;
            font-size: 11px;
        }
        
        .flag.green {
            background-color: #d4edda;
            color: #155724;
        }
        
        .flag.red {
            background-color: #f8d7da;
            color: #721c24;
        }
        
        .link-button {
            display: inline-block;
            background-color: #3498db;
            color: #ffffff;
            padding: 10px 20px;
            text-decoration: none;
            margin-top: 10px;
            font-weight: bold;
        }
        
        ul {
            line-height: 1.8;
            margin: 10px 0;
            padding-left: 20px;
        }
        
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
            font-size: 12px;
            color: #7f8c8d;
        }
        
        .error-box {
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
        }
        
        /* Mobile responsive */
        @media only screen and (max-width: 600px) {
            .email-container {
                width: 100% !important;
            }
            .content {
                padding: 20px !important;
            }
            h1 {
                font-size: 20px !important;
            }
            h2 {
                font-size: 18px !important;
            }
        }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="content">
"""

    def _html_executive_summary(
        self,
        run_date: datetime,
        total_opportunities: int,
        high_priority: list[Opportunity],
        runtime_seconds: float,
        estimated_cost: float,
    ) -> str:
        """Generate executive summary section."""
        highest_score = max([o.opportunity_score for o in high_priority], default=0)
        highest_edge = max([o.edge for o in high_priority], default=0)

        return f"""
        <h1>Polymarket Trading Opportunities</h1>
        <p><strong>Date:</strong> {run_date.strftime('%A, %B %d, %Y')}</p>

        <div class="summary-box">
            <h3>Executive Summary</h3>
            <p><strong>{total_opportunities}</strong> opportunities identified</p>
            <p><strong>{len(high_priority)}</strong> high-priority opportunities</p>
            <p><strong>Highest Edge:</strong> {highest_edge:.1%}</p>
            <p><strong>Best Opportunity Score:</strong> {highest_score:.4f}</p>
            <p><strong>Runtime:</strong> {runtime_seconds/60:.1f} minutes</p>
            <p><strong>Estimated Cost:</strong> ${estimated_cost:.2f}</p>
        </div>
"""

    def _html_high_priority_section(self, opportunities: list[Opportunity]) -> str:
        """Generate high priority opportunities section."""
        html = """
        <h2>High Priority Opportunities</h2>
        <p>These opportunities show strong potential based on research and model estimates.</p>
"""

        for opp in opportunities:
            html += self._html_opportunity_card(opp)

        return html

    def _html_medium_priority_section(self, opportunities: list[Opportunity]) -> str:
        """Generate medium priority opportunities section."""
        html = """
        <h2>Medium Priority Opportunities</h2>
        <p>These opportunities show moderate potential and may be worth monitoring.</p>
"""

        for opp in opportunities:
            html += self._html_opportunity_card(opp, priority="medium")

        return html

    def _html_opportunity_card(self, opp: Opportunity, priority: str = "high") -> str:
        """Generate HTML for a single opportunity."""
        class_name = "opportunity" if priority == "high" else "opportunity medium"

        # Prepare metrics
        metrics = f"""
            <span class="metric">Model: {opp.model_probability:.1%}</span>
            <span class="metric">Market: {opp.market_probability:.1%}</span>
            <span class="metric edge">Edge: {opp.edge:.1%}</span>
            <span class="metric score">Score: {opp.opportunity_score:.4f}</span>
            <span class="metric confidence">Confidence: {opp.confidence_score.overall_score:.2f}</span>
        """

        # Prepare flags
        flags_html = ""
        for flag in opp.green_flags:
            flags_html += f'<span class="flag green">✓ {flag}</span>'
        for flag in opp.red_flags:
            flags_html += f'<span class="flag red">⚠ {flag}</span>'

        # Key findings
        findings_html = "<ul>"
        for finding in opp.tier2_research.key_findings[:5]:
            findings_html += f"<li>{finding.finding[:200]}...</li>"
        findings_html += "</ul>"

        return f"""
        <div class="{class_name}">
            <h3>{opp.question}</h3>

            <p><strong>Recommendation:</strong> {opp.recommended_action} {opp.recommended_outcome}</p>

            <div>{metrics}</div>

            <p><strong>Volume:</strong> ${opp.market.volume:,.0f} |
               <strong>Liquidity:</strong> ${opp.market.liquidity:,.0f} |
               <strong>Resolves:</strong> {opp.market.end_date.strftime('%Y-%m-%d')}</p>

            <div><strong>Key Findings:</strong></div>
            {findings_html}

            <div><strong>Reasoning:</strong></div>
            <p>{opp.tier2_research.reasoning[:500]}...</p>

            {f'<div><strong>Flags:</strong><br>{flags_html}</div>' if flags_html else ''}

            <a href="{opp.polymarket_url}" class="link-button" target="_blank">View on Polymarket</a>
        </div>
"""

    def _html_errors_section(self, errors: list[str]) -> str:
        """Generate errors section if any."""
        html = """
        <h2>System Notices</h2>
        <div class="error-box">
            <ul>
"""
        for error in errors[:10]:  # Limit to 10 errors
            html += f"<li>{error}</li>"

        html += """
            </ul>
        </div>
"""
        return html

    def _html_footer(self, run_date: datetime, runtime_seconds: float) -> str:
        """Generate footer."""
        return f"""
        <div class="footer">
            <p>Generated with Claude Code on {run_date.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            <p>Total runtime: {runtime_seconds/60:.1f} minutes</p>
            <p><em>This is an automated research report. Always conduct your own due diligence before trading.</em></p>
        </div>
        </div>
    </div>
</body>
</html>
"""
