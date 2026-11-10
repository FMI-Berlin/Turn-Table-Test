"""Trusted display equations, rendered natively in PDF and offline HTML."""
import html

# Only named, project-owned equations are accepted; Markdown is never executed as TeX.
EQUATIONS = {
    'circle': (
        r'\begin{aligned} E^*(t)&=E_c+R\cos\theta(t), & N^*(t)&=N_c+R\sin\theta(t),\\ e_E(t)&=E(t)-E^*(t), & e_N(t)&=N(t)-N^*(t).\end{aligned}',
        '<mtable columnalign="left"><mtr><mtd><msup><mi>E</mi><mo>*</mo></msup><mo>(</mo><mi>t</mi><mo>)</mo><mo>=</mo><msub><mi>E</mi><mi>c</mi></msub><mo>+</mo><mi>R</mi><mi>cos</mi><mi>θ</mi><mo>(</mo><mi>t</mi><mo>)</mo><mo>,</mo><mspace width="1em"/><msup><mi>N</mi><mo>*</mo></msup><mo>(</mo><mi>t</mi><mo>)</mo><mo>=</mo><msub><mi>N</mi><mi>c</mi></msub><mo>+</mo><mi>R</mi><mi>sin</mi><mi>θ</mi><mo>(</mo><mi>t</mi><mo>)</mo></mtd></mtr><mtr><mtd><msub><mi>e</mi><mi>E</mi></msub><mo>=</mo><mi>E</mi><mo>−</mo><msup><mi>E</mi><mo>*</mo></msup><mo>,</mo><mspace width="1em"/><msub><mi>e</mi><mi>N</mi></msub><mo>=</mo><mi>N</mi><mo>−</mo><msup><mi>N</mi><mo>*</mo></msup></mtd></mtr></mtable>',
        'Expected circle coordinates and horizontal residuals'),
    'hrms': (
        r'\mathrm{HRMS}_j=\sqrt{\frac{1}{n_j}\sum_{k\in\mathcal B_j}\left(e_{E,k}^{\,2}+e_{N,k}^{\,2}\right)},\qquad n_j=|\mathcal B_j|.',
        '<msub><mtext>HRMS</mtext><mi>j</mi></msub><mo>=</mo><msqrt><mfrac><mn>1</mn><msub><mi>n</mi><mi>j</mi></msub></mfrac><munder><mo>∑</mo><mrow><mi>k</mi><mo>∈</mo><msub><mi>ℬ</mi><mi>j</mi></msub></mrow></munder><mrow><mo>(</mo><msubsup><mi>e</mi><mrow><mi>E</mi><mo>,</mo><mi>k</mi></mrow><mn>2</mn></msubsup><mo>+</mo><msubsup><mi>e</mi><mrow><mi>N</mi><mo>,</mo><mi>k</mi></mrow><mn>2</mn></msubsup><mo>)</mo></mrow></msqrt><mo>,</mo><mspace width="1em"/><msub><mi>n</mi><mi>j</mi></msub><mo>=</mo><mo>|</mo><msub><mi>ℬ</mi><mi>j</mi></msub><mo>|</mo>',
        'Horizontal RMS in bin j; n j is its epoch count'),
    'fit': (
        r'\begin{aligned}(\hat a,\hat b)&=\underset{a,b}{\operatorname{arg\,min}}\sum_{j=1}^{J}(y_j-a-bx_j)^2,\\ \hat y(x)&=\hat a+\hat b x,\qquad [y_j]=\mathrm{mm},\quad [x_j]=\mathrm{s},\quad [\hat b]=\mathrm{mm\,s^{-1}}.\end{aligned}',
        '<mtable columnalign="left"><mtr><mtd><mo>(</mo><mover><mi>a</mi><mo>^</mo></mover><mo>,</mo><mover><mi>b</mi><mo>^</mo></mover><mo>)</mo><mo>=</mo><munder><mtext>arg min</mtext><mrow><mi>a</mi><mo>,</mo><mi>b</mi></mrow></munder><munderover><mo>∑</mo><mrow><mi>j</mi><mo>=</mo><mn>1</mn></mrow><mi>J</mi></munderover><msup><mrow><mo>(</mo><msub><mi>y</mi><mi>j</mi></msub><mo>−</mo><mi>a</mi><mo>−</mo><mi>b</mi><msub><mi>x</mi><mi>j</mi></msub><mo>)</mo></mrow><mn>2</mn></msup></mtd></mtr><mtr><mtd><mover><mi>y</mi><mo>^</mo></mover><mo>(</mo><mi>x</mi><mo>)</mo><mo>=</mo><mover><mi>a</mi><mo>^</mo></mover><mo>+</mo><mover><mi>b</mi><mo>^</mo></mover><mi>x</mi><mo>,</mo><mspace width="1em"/><mtext>y in mm; x in s; slope in mm/s</mtext></mtd></mtr></mtable>',
        'Unweighted least squares across bins with a free intercept'),
    'height': (
        r'h_k=H_{\mathrm{GGA},k}+\mathcal N_{\mathrm{GGA},k},\qquad \Delta h_k=h_{\mathrm{rover},k}-h_{\mathrm{ref}}(t_k).',
        '<msub><mi>h</mi><mi>k</mi></msub><mo>=</mo><msub><mi>H</mi><mrow><mtext>GGA</mtext><mo>,</mo><mi>k</mi></mrow></msub><mo>+</mo><msub><mi>𝒩</mi><mrow><mtext>GGA</mtext><mo>,</mo><mi>k</mi></mrow></msub><mo>,</mo><mspace width="1em"/><msub><mrow><mi>Δ</mi><mi>h</mi></mrow><mi>k</mi></msub><mo>=</mo><msub><mi>h</mi><mrow><mtext>rover</mtext><mo>,</mo><mi>k</mi></mrow></msub><mo>−</mo><msub><mi>h</mi><mtext>ref</mtext></msub><mo>(</mo><msub><mi>t</mi><mi>k</mi></msub><mo>)</mo>',
        'Ellipsoidal height from GGA altitude and geoid separation; relative height residual'),
    'vrms': (
        r'\mathrm{VRMS}_j=\sqrt{\frac{1}{n_j}\sum_{k\in\mathcal B_j}(\Delta h_k)^2}.',
        '<msub><mtext>VRMS</mtext><mi>j</mi></msub><mo>=</mo><msqrt><mfrac><mn>1</mn><msub><mi>n</mi><mi>j</mi></msub></mfrac><munder><mo>∑</mo><mrow><mi>k</mi><mo>∈</mo><msub><mi>ℬ</mi><mi>j</mi></msub></mrow></munder><msup><mrow><mo>(</mo><msub><mrow><mi>Δ</mi><mi>h</mi></mrow><mi>k</mi></msub><mo>)</mo></mrow><mn>2</mn></msup></msqrt>',
        'Vertical RMS in bin j, with the mean offset retained'),
    'bias': (
        r'\begin{aligned}\mu_h&=\frac{1}{n}\sum_{k=1}^{n}\Delta h_k,& \sigma_h&=\sqrt{\frac{1}{n}\sum_{k=1}^{n}(\Delta h_k-\mu_h)^2},\\ \mathrm{VRMS}^2&=\mu_h^2+\sigma_h^2.\end{aligned}',
        '<mtable columnalign="left"><mtr><mtd><msub><mi>μ</mi><mi>h</mi></msub><mo>=</mo><mfrac><mn>1</mn><mi>n</mi></mfrac><munderover><mo>∑</mo><mrow><mi>k</mi><mo>=</mo><mn>1</mn></mrow><mi>n</mi></munderover><msub><mrow><mi>Δ</mi><mi>h</mi></mrow><mi>k</mi></msub><mo>,</mo><mspace width="1em"/><msub><mi>σ</mi><mi>h</mi></msub><mo>=</mo><msqrt><mfrac><mn>1</mn><mi>n</mi></mfrac><munderover><mo>∑</mo><mrow><mi>k</mi><mo>=</mo><mn>1</mn></mrow><mi>n</mi></munderover><msup><mrow><mo>(</mo><msub><mrow><mi>Δ</mi><mi>h</mi></mrow><mi>k</mi></msub><mo>−</mo><msub><mi>μ</mi><mi>h</mi></msub><mo>)</mo></mrow><mn>2</mn></msup></msqrt></mtd></mtr><mtr><mtd><msup><mtext>VRMS</mtext><mn>2</mn></msup><mo>=</mo><msubsup><mi>μ</mi><mi>h</mi><mn>2</mn></msubsup><mo>+</mo><msubsup><mi>σ</mi><mi>h</mi><mn>2</mn></msubsup></mtd></mtr></mtable>',
        'Mean height bias, population standard deviation and RMS decomposition'),
    'rotation': (
        r'\overline T=\frac{1}{K}\sum_{k=1}^{K}T_k,\qquad \omega=\frac{360^{\circ}}{\overline T}.',
        '<mover><mi>T</mi><mo>¯</mo></mover><mo>=</mo><mfrac><mn>1</mn><mi>K</mi></mfrac><munderover><mo>∑</mo><mrow><mi>k</mi><mo>=</mo><mn>1</mn></mrow><mi>K</mi></munderover><msub><mi>T</mi><mi>k</mi></msub><mo>,</mo><mspace width="1em"/><mi>ω</mi><mo>=</mo><mfrac><mrow><mn>360</mn><mo>°</mo></mrow><mover><mi>T</mi><mo>¯</mo></mover></mfrac>',
        'Effective angular rate from the mean complete-revolution period'),
    'windup': (
        r'\begin{aligned}\left|\dot L_{\mathrm{WU},i}\right|&=\lambda_i\frac{|\omega|}{360^{\circ}},\\ \left[\dot L_{\mathrm{WU},i}\right]&=\mathrm{mm\,s^{-1}}\quad(\lambda_i\text{ in mm},\ \omega\text{ in degrees/s}).\end{aligned}',
        '<mo>|</mo><msub><mover><mi>L</mi><mo>˙</mo></mover><mrow><mtext>WU</mtext><mo>,</mo><mi>i</mi></mrow></msub><mo>|</mo><mo>=</mo><msub><mi>λ</mi><mi>i</mi></msub><mfrac><mrow><mo>|</mo><mi>ω</mi><mo>|</mo></mrow><mrow><mn>360</mn><mo>°</mo></mrow></mfrac><mo>,</mo><mspace width="1em"/><mtext>λ in mm; ω in degrees/s; result in mm/s</mtext>',
        'Magnitude of the ideal axial-rotation wind-up contribution'),
}


def equation_html(name):
    _, body, description = EQUATIONS[name]
    return '<div class="equation"><math xmlns="http://www.w3.org/1998/Math/MathML" display="block" alttext="'+html.escape(description,quote=True)+'"><mrow>'+body+'</mrow></math></div>'


def equation_latex(name):
    return EQUATIONS[name][0]
