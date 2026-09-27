package com.tsunami.shell.brand

import androidx.compose.foundation.Canvas
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.graphics.Path
import com.tsunami.shell.theme.LocalTsunamiPalette
import kotlin.math.min

/**
 * TSUNAMI master mark rendered from the same normalized geometry as brand/tsunami-mark.svg.
 *
 * Source viewBox: 1000 × 820
 * Outer arch circle: center (500, 509.61), r=509.61
 * Inner optical counter: center (500, 502.69), r=394.61
 * Terminal baseline: y=411.11
 * Body circle: center (500, 531), r=289
 *
 * The path is scaled uniformly and centered; callers cannot accidentally distort the mark.
 */
@Composable
fun TsunamiMark(modifier: Modifier = Modifier) {
    val p = LocalTsunamiPalette.current
    Canvas(modifier) {
        val sourceW = 1000f
        val sourceH = 820f
        val scale = min(size.width / sourceW, size.height / sourceH)
        val dx = (size.width - sourceW * scale) / 2f
        val dy = (size.height - sourceH * scale) / 2f

        fun sx(x: Float) = dx + x * scale
        fun sy(y: Float) = dy + y * scale
        fun rect(cx: Float, cy: Float, r: Float) = Rect(
            left = sx(cx - r),
            top = sy(cy - r),
            right = sx(cx + r),
            bottom = sy(cy + r),
        )

        val arch = Path().apply {
            moveTo(sx(0f), sy(411.11f))
            arcTo(
                rect = rect(500f, 509.61f, 509.61f),
                startAngleDegrees = 191.14456f,
                sweepAngleDegrees = 157.71088f,
                forceMoveTo = false,
            )
            lineTo(sx(883.84f), sy(411.11f))
            arcTo(
                rect = rect(500f, 502.69f, 394.61f),
                startAngleDegrees = 346.58072f,
                sweepAngleDegrees = -153.16145f,
                forceMoveTo = false,
            )
            close()
        }

        drawPath(arch, p.ink)
        drawCircle(
            color = p.ink,
            radius = 289f * scale,
            center = Offset(sx(500f), sy(531f)),
        )
    }
}
