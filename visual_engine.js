/**
 * VISUAL INTELLIGENCE ENGINE
 * Core analytical algorithms for the Freshbus CX Analytics Dashboard
 */

const VisualEngine = (function() {
    
    // --- PEARSON CORRELATION ENGINE ---
    function calcCorrelation(arr1, arr2) {
        if (!arr1 || !arr2 || arr1.length !== arr2.length || arr1.length < 7) return null;
        
        let sum1 = 0, sum2 = 0, sum1Sq = 0, sum2Sq = 0, pSum = 0;
        let n = arr1.length;
        
        for (let i = 0; i < n; i++) {
            sum1 += arr1[i];
            sum2 += arr2[i];
            sum1Sq += Math.pow(arr1[i], 2);
            sum2Sq += Math.pow(arr2[i], 2);
            pSum += (arr1[i] * arr2[i]);
        }
        
        let num = pSum - (sum1 * sum2 / n);
        let den = Math.sqrt((sum1Sq - Math.pow(sum1, 2) / n) * (sum2Sq - Math.pow(sum2, 2) / n));
        
        if (den === 0) return 0;
        return num / den;
    }
    
    function getRelationshipStrength(r) {
        if (r === null) return "Insufficient Data";
        let abs = Math.abs(r);
        if (abs < 0.3) return "Weak";
        if (abs < 0.5) return "Moderate";
        if (abs < 0.7) return "Strong";
        return "Very Strong";
    }

    function analyzeRelationship(metricA, metricB, chartData) {
        if (!chartData || chartData.length < 7) return null;
        
        const arr1 = chartData.map(d => Number(d[metricA]) || 0);
        const arr2 = chartData.map(d => Number(d[metricB]) || 0);
        
        const r = calcCorrelation(arr1, arr2);
        
        return {
            metricA,
            metricB,
            correlation: r ? r.toFixed(2) : null,
            direction: r && r > 0 ? "Positive" : (r ? "Negative" : "None"),
            strength: getRelationshipStrength(r),
            observations: arr1.length
        };
    }

    // --- ATTENTION SCORING ENGINE ---
    const BASE_WEIGHTS = {
        "net_abn_pct": 1.5,
        "sl_pct": 1.5,
        "aht": 1.3,
        "repeat_pct": 1.3,
        "avg_wait": 1.3
    };

    function calculateAttentionScores(chartData) {
        if (!chartData || chartData.length < 2) return [];
        
        let scores = [];
        let latest = chartData[chartData.length - 1];
        let previous = chartData[chartData.length - 2];
        
        Object.keys(BASE_WEIGHTS).forEach(metric => {
            if (latest[metric] !== undefined && previous[metric] !== undefined) {
                let currentVal = latest[metric];
                let prevVal = previous[metric];
                let diff = currentVal - prevVal;
                
                // For SL, lower is worse. For others, higher is worse.
                let isDeterioration = metric === "sl_pct" ? diff < 0 : diff > 0;
                
                if (isDeterioration) {
                    let severity = Math.abs(diff) / (prevVal || 1); // simple % change
                    
                    // Check persistence (3 periods)
                    let persistence = 1.0;
                    if (chartData.length >= 3) {
                        let p2 = chartData[chartData.length - 3][metric];
                        let diff2 = prevVal - p2;
                        let isDet2 = metric === "sl_pct" ? diff2 < 0 : diff2 > 0;
                        if (isDet2) {
                            persistence = 1.15;
                            if (chartData.length >= 4) {
                                let p3 = chartData[chartData.length - 4][metric];
                                let diff3 = p2 - p3;
                                let isDet3 = metric === "sl_pct" ? diff3 < 0 : diff3 > 0;
                                if (isDet3) persistence = 1.30;
                            }
                        }
                    }
                    
                    let rawScore = severity * BASE_WEIGHTS[metric] * persistence * 100;
                    
                    scores.push({
                        metric: metric,
                        value: currentVal,
                        movement: diff,
                        persistence: persistence,
                        score: Math.min(Math.round(rawScore), 100)
                    });
                }
            }
        });
        
        return scores.sort((a, b) => b.score - a.score);
    }

    return {
        analyzeRelationship,
        calculateAttentionScores
    };

})();

window.VisualEngine = VisualEngine;
