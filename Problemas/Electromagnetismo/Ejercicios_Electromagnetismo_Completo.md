# Compilación Completa de Ejercicios de Electromagnetismo

Este documento unifica todas las hojas de ejercicios del curso de Electromagnetismo (3º de Física).

---

# Tema 1: Cálculo Vectorial y Campo Electrostático

## Hoja 1: Cálculo Vectorial

### 1.- Expresión de campos escalares
Exprese los siguientes campos escalares en coordenadas cartesianas, cilíndricas y esféricas:
a) $\phi = \frac{x^2 + y^2 + z^2}{2}$
b) $\phi = 2z^2 - x^2 - y^2$
c) $\phi = \frac{z \sin\phi}{\rho}$
d) $\phi = \cot\theta - \tan\theta$

### 2.- Expresión de campos vectoriales
Expresar los siguientes campos vectoriales en coordenadas cartesianas, cilíndricas y esféricas:
a) $\vec{F} = \vec{r}$
b) $\vec{F} = (x^2 + y^2)\vec{u}_x + (x^2 - y^2)\vec{u}_y$
c) $\vec{F} = (\rho^2 - z^2)\vec{u}_\rho - 2\rho z \vec{u}_z$
d) $\vec{F} = r \tan\theta \vec{u}_\theta$

### 3.- Operaciones vectoriales en un punto
Dados los vectores $\vec{A} = \vec{u}_\rho - \vec{u}_z$ y $\vec{B} = 12\vec{u}_\theta + 5\vec{u}_r$, evaluados en el punto $P(3, 4, 12)$ (en cartesianas), calcular:
a) $\vec{A} + \vec{B}$
b) $\vec{A} \cdot \vec{B}$
c) $\vec{A} \times \vec{B}$

### 4.- Cálculo de gradientes
Calcular el gradiente en coordenadas cartesianas, cilíndricas y esféricas de los campos escalares:
a) $\phi = \frac{x^2 + y^2 + z^2}{2}$
b) $\phi = 2z^2 - x^2 - y^2$

### 5.- Gradiente del vector de posición
Hallar el gradiente del módulo del vector de posición $\vec{r}$.

### 6.- Divergencia y rotacional
Hallar la divergencia y el rotacional del vector de posición $\vec{r}$.

### 7.- Demostración de identidad con gradiente
Demostrar que:
$$\nabla \left( \frac{1}{r^3} \vec{r} \right) = 0 \quad (\text{para } r \neq 0)$$
*Nota: También se puede interpretar como demostrar la identidad $\nabla(r^{-3}) = -3 r^{-5} \vec{r}$.*

### 8.- Laplaciano de 1/r
Obtener la expresión de la Laplaciana de $1/r$ en todo el espacio.

### 9.- Perpendicularidad del gradiente
Probar que $\vec{\nabla}V$ es un vector perpendicular a la superficie $V(x,y,z) = \text{cte.}$

### 10.- Vector normal a superficie
Encontrar en el punto $P(3, -1, 2)$ el vector unitario normal a la superficie:
$$2x^2 + 4yz - 5z^2 = -10$$

### 11.- Derivada direccional
Sea $V = x^2yz + y^3 - z^3$, calcular su derivada direccional en el punto $(2,1,3)$ en la dirección dada por el vector $2\vec{i} - 2\vec{j} + \vec{k}$.

### 12.- Gradiente de función radial
Demostrar que, si $V(\vec{r}) = V(r)$, entonces:
$$\vec{\nabla}V = \frac{1}{r} \frac{dV}{dr}\vec{r} = \frac{dV}{dr}\vec{u}_r$$

### 13.- Identidades del operador nabla
Comprobar las siguientes identidades vectoriales:
a) $\vec{\nabla} \cdot (V\vec{A}) = V \vec{\nabla} \cdot \vec{A} + \vec{A} \cdot \vec{\nabla}V$
b) $\vec{\nabla} \times (V\vec{A}) = V \vec{\nabla} \times \vec{A} + \vec{\nabla}V \times \vec{A}$
c) $\vec{\nabla} \cdot (\vec{A} \times \vec{B}) = \vec{B} \cdot (\vec{\nabla} \times \vec{A}) - \vec{A} \cdot (\vec{\nabla} \times \vec{B})$

### 14.- Nulidad de operaciones sucesivas
Demostrar que:
$$\vec{\nabla} \cdot (\vec{\nabla} \times \vec{A}) = 0 \quad \text{y} \quad \vec{\nabla} \times (\vec{\nabla}V) = 0$$

### 15.- Cálculo sobre campos específicos
Dados los campos $V(\vec{r}) = x^2y^2z^2$ y $\vec{A}(\vec{r}) = x^2y\vec{i} + xz^3\vec{j} - y^2z^2\vec{k}$, calcular:
$$\vec{\nabla}V, \quad \vec{\nabla} \cdot \vec{A}, \quad \vec{\nabla} \times \vec{A}, \quad \vec{\nabla} \cdot (V\vec{A}), \quad \vec{\nabla} \times (V\vec{A}), \quad \nabla^2V, \quad \nabla^2\vec{A}, \quad \vec{\nabla}(\vec{\nabla} \cdot \vec{A}) \quad \text{y} \quad \vec{\nabla} \times (\vec{\nabla} \times \vec{A})$$

### 16.- Operaciones adicionales sobre campos
Para los campos $V(\vec{r}) = x^2yz^3$ y $\vec{A}(\vec{r}) = xz\vec{i} - y^2\vec{j} + 2x^2y\vec{k}$, calcular:
$$\vec{\nabla}V, \quad \vec{\nabla} \cdot \vec{A}, \quad \vec{\nabla} \times \vec{A}, \quad \vec{\nabla} \cdot (V\vec{A}) \quad \text{y} \quad \vec{\nabla} \times (V\vec{A})$$

### 17.- Teorema de la Divergencia en un cubo
Calcular, directamente y mediante el teorema de la divergencia, la integral:
$$\iint_S \vec{F} \cdot d\vec{s}$$
siendo $\vec{F} = x\vec{i}$ y $S$ la superficie de un cubo de lado $a$. ¿Depende de la posición del cubo?

### 18.- Flujo a través de varias superficies
Dado el campo vectorial $\vec{F} = x^3\vec{i} + y^3\vec{j} + z^3\vec{k}$, calcular su flujo a través de las siguientes superficies cerradas:
a) Un cubo de arista $a$, con un vértice en el origen y aristas a lo largo de los ejes positivos ($a\vec{i}, a\vec{j}, a\vec{k}$).
b) Un cilindro de superficie lateral $x^2 + y^2 = 4$ y sus bases en los planos $z = -1, z = 2$.
c) Una esfera de radio $R$ centrada en el origen de coordenadas.

### 19.- Teorema de Stokes en plano z=0
Sea $\vec{F} = (x^2 - y^3)\vec{i} + xy^3\vec{j} + xyz^2\vec{k}$, aplíquese el teorema de Stokes para el cálculo de:
$$\oint_C \vec{F} \cdot d\vec{\ell}$$
donde $C$ es la curva cerrada limitada por el eje X y las rectas $x = y$, $x = 3$, contenida en el plano $z = 0$.

### 20.- Circulación de un campo vectorial
Calcular, directamente y mediante el teorema de Stokes, la circulación del campo vectorial:
$$\vec{A} = xy^2\vec{i} + x^2\vec{j}$$
a lo largo de las siguientes curvas cerradas:
a) El triángulo de vértices en los puntos $(0, 0)$, $(a,0)$ y $(a, a)$.
b) La circunferencia de radio $R$ en el plano $z = 0$, con centro en el origen de coordenadas.

### 21.- Integral de superficie en una esfera
Hallar el valor de la integral:
$$\iint_S \vec{A} \cdot d\vec{s}$$
con $\vec{A} = \cot\theta \vec{u}_r - \vec{u}_\theta$, siendo la superficie de integración una esfera de radio $R$ centrada en el origen.

---

## Hoja 2: Campo Electrostático

### 1.- Hexágono regular de cargas
Sobre los vértices de un hexágono regular de lado $a$ se sitúan seis cargas puntuales iguales de valor $q$. ¿Qué carga habrá que depositar en el centro de dicho hexágono para que el sistema se mantenga en equilibrio electrostático?

### 2.- Cargas en circunferencia y eje Z
En el plano XY se depositan cuatro cargas puntuales iguales $q$ uniformemente espaciadas sobre una circunferencia de radio $a$ centrada en el origen de coordenadas. Sobre el eje Z se tienen dos cargas iguales de valor $Q_2$, distanciadas $2a$ y equidistantes del origen de coordenadas, donde se encuentra una carga $Q_1$.
Siendo fijo el valor $q$, ¿qué cargas $Q_1$ y $Q_2$ son necesarias para que el sistema descrito se halle en equilibrio electrostático?

### 3.- Estabilidad de cargas en circunferencia
Una carga puntual $q$ se coloca en el centro de una circunferencia de radio $a$, mientras que $N$ cargas puntuales iguales de valor $-q$ se colocan uniformemente espaciadas sobre dicha circunferencia. Si las soltamos simultáneamente, estas cargas pueden converger hacia el centro, o bien divergir. Obtener la relación que determina un comportamiento u otro, y calcular el valor de $N$ que constituye la frontera entre ambos comportamientos.

### 4.- Campo de polígono regular de cargas
Se sitúan $N$ cargas puntuales iguales de valor $q$ sobre una circunferencia de radio $a$, de manera que sus posiciones corresponden a los vértices de un polígono regular ($N$ lados). Calcular el campo electrostático en un punto del eje perpendicular a la circunferencia.

### 5.- Anillo uniformemente cargado
Una carga $q$ se encuentra uniformemente distribuida sobre un anillo de radio $a$. Calcular el campo y el potencial electrostáticos en puntos situados sobre el eje.

### 6.- Corona circular cargada
Una corona circular, limitada por circunferencias de radios interior $a$ y exterior $b$ ($a < b$), tiene una densidad de carga superficial $\sigma_0$ uniforme. Calcular el campo electrostático $\vec{E}$ en los puntos del eje.

### 7.- Varilla finita cargada
Calcular el campo eléctrico debido a una varilla finita de longitud $L$ con densidad lineal de carga $\lambda_0$ uniforme.

### 8.- Tira plana infinita
Calcular el campo electrostático en el plano bisector de una tira, muy larga y de anchura $2a$, con densidad superficial de carga $\sigma_0$ uniforme.

### 9.- Superficie esférica cargada
Calcular el campo eléctrico en cualquier punto del espacio debido a una distribución uniforme de carga sobre una superficie esférica de radio $a$ de densidad uniforme $\sigma$.

### 10.- Superficie cilíndrica cargada de longitud finita
Sobre la superficie lateral de un cilindro de radio $a$ y longitud $2L$, existe carga con densidad superficial $\sigma_0$ uniforme. Calcular el campo electrostático $\vec{E}$ en puntos del eje.

### 11.- Cilindro macizo cargado de longitud finita
En un volumen cilíndrico de radio $a$ y longitud $2L$, existe carga con densidad $\rho_0$ uniforme. Calcular el campo eléctrico en puntos del eje.

### 12.- Campo nulo por superposición de hilo e hilo curvo
Se dispone un hilo rectilíneo infinito, uniformemente cargado con densidad $\lambda_0$, a una distancia $R$ del centro de un hilo semicircular de radio $R$. Sobre el alambre curvo la densidad de carga es no uniforme y directamente proporcional a $1 + \sin\theta$ (ver figura). Sabiendo que el campo eléctrico resulta ser nulo en el punto $O$ (centro de la semicircunferencia), ¿qué valor tiene la carga total depositada sobre la distribución semicircular?

### 13.- Plano con densidad variable
Sobre una superficie plana de gran tamaño se deposita carga eléctrica con una densidad superficial expresada en coordenadas polares:
$$\sigma(r) = \frac{\sigma_0 a}{r}$$
donde $a$ (m) y $\sigma_0$ ($\text{C/m}^2$) son constantes. Determinar el campo eléctrico $\vec{E}$ en el eje de simetría (eje Z).

### 14.- Esfera con densidad radial variable
Calcular el campo eléctrico $\vec{E}$ en cualquier punto del espacio debido a una distribución de carga esférica de radio $a$ de densidad en volumen $\rho = A r^2$, siendo $A$ ($\text{C/m}^5$) constante.

### 15.- Esfera con densidad dipolar superficial
Calcular el campo electrostático $\vec{E}$ en el centro de una esfera de radio $a$ y densidad superficial de carga dada por $\sigma = A \cos\theta$, siendo constante $A$ ($\text{C/m}^2$).

### 16.- Placa con densidad linealmente variable
En la región del espacio limitada por los planos $x = 0$ y $x = d$ existe una distribución de carga no uniforme de densidad $\rho(x) = \rho_0 \frac{x}{d}$. Calcular el campo electrostático $\vec{E}$ en cualquier punto.

---

## Hoja 3: Ley de Gauss

### 1.- Corteza esférica con densidad uniforme
Una corteza esférica de radios $a$ y $b$ ($a < b$), posee una densidad volúmica de carga $\rho_0$ uniforme. Calcular el campo electrostático en cualquier punto del espacio.

### 2.- Esfera con densidad lineal radial
Calcular el campo y el potencial electrostáticos en cualquier punto del espacio debidos a la distribución de carga en volumen no uniforme de densidad:
$$\rho(r) = \begin{cases} \rho_0 \frac{r}{a} & \text{si } r \le a \\ 0 & \text{si } r > a \end{cases}$$
expresada en coordenadas esféricas.

### 3.- Esfera con densidad exponencial
Calcular el campo y el potencial electrostáticos en cualquier punto del espacio debidos a la distribución de carga en volumen no uniforme de densidad:
$$\rho(r) = \rho_0 e^{-r/a}$$
expresada en coordenadas esféricas.

### 4.- Condensador esférico
Dos superficies esféricas poseen cargas iguales de signo contrario y se disponen concéntricas. La corteza interior tiene un radio $a$ y carga $+q$, la exterior un radio $b$ y carga $-q$. Hallar la diferencia de potencial entre ambas.

### 5.- Cilindro infinito superficialmente cargado
Calcular el campo y el potencial electrostáticos debidos a una distribución de carga de densidad uniforme $\sigma_0$ depositada sobre una superficie cilíndrica de radio $a$ y longitud infinita.

### 6.- Cilindros concéntricos coaxiales
Consideremos dos superficies cilíndricas muy largas, de radios $a$ y $b$ ($a < b$), con densidades de carga $\sigma_1$ y $\sigma_2$, respectivamente. Calcular el campo eléctrico en cualquier punto. ¿Existe alguna relación entre $\sigma_1$ y $\sigma_2$ que hace nulo el campo en la zona exterior?

### 7.- Cilindro infinito macizo uniformemente cargado
Sobre una región cilíndrica de radio $a$ y longitud infinita existe una distribución volúmica de carga de densidad uniforme $\rho_0$. Calcular el campo y el potencial electrostáticos en cualquier punto del espacio.

### 8.- Cilindro infinito con densidad lineal radial
Calcular el campo eléctrico en cualquier punto del espacio debido a una región cilíndrica, de longitud infinita, con una distribución volúmica de carga de densidad no uniforme:
$$\rho(r) = \begin{cases} \rho_0 \frac{r}{a} & \text{si } r \le a \\ 0 & \text{si } r > a \end{cases}$$
expresada en coordenadas cilíndricas.

### 9.- Distribución plana con simetría de placa
Mediante la aplicación de la Ley de Gauss, calcular el campo eléctrico correspondiente a la siguiente distribución volúmica de carga con simetría plana:
$$\rho(x, y, z) = \begin{cases} \rho_0 & \text{si } -d \le x \le d \\ 0 & \text{si } |x| > d \end{cases}$$

### 10.- Unión p-n semiconductora
El funcionamiento de buena parte de los dispositivos semiconductores se basa en la "unión pn", que puede modelarse como una distribución de carga:
$$\rho(x) = \begin{cases} +\rho_0 & \text{si } -a < x < 0 \\ -\rho_0 & \text{si } 0 < x < a \\ 0 & \text{resto del espacio} \end{cases}$$
Mediante la aplicación de la Ley de Gauss, calcular el campo eléctrico en el interior del semiconductor, así como la diferencia de potencial entre sus extremos.
*Datos de nota:* suponer que $a = 300\,\text{nm}$ y $\rho_0 = 120\,\text{C/m}^3$.

---

## Hoja 4: Campo y Potencial Electrostáticos

### 1.- Fuerza y potencial de dos cargas sobre eje X
Dos cargas puntuales de valor $q_1$ y $q_2$ se sitúan distanciadas $2d$ sobre el eje X y equidistantes del origen de coordenadas. Se pide:
a) Calcular la fuerza electrostática que ejercen sobre una carga puntual $Q$ situada en el eje Y.
b) Situada la carga $Q$ en $y = 0$, obtener el valor del potencial electrostático en dicho punto. ¿Qué trabajo ha sido necesario para traer $Q$ desde un punto muy lejano?

### 2.- Trabajo para cargar vértice de un cono
Una superficie cónica de radio en la base $R$ y de gran altura $h$ tiene una carga uniformemente distribuida en su superficie lateral, de densidad $\sigma$. Determinar el trabajo necesario para trasladar una carga $q$ desde un punto muy alejado hasta el vértice del cono.

### 3.- Propiedades de un campo electrostático plano
Un cierto campo eléctrico se representa por:
$$\vec{E} = a x \vec{i} - b \vec{j}$$
siendo $a = 2\,\text{V/m}^2$ y $b = 1\,\text{V/m}$. Calcular:
a) El potencial eléctrico $V$ en cualquier punto del plano XY tomando el origen de potenciales en $(0,0)$.
b) El trabajo proporcionado por el campo si una carga $q = 10^{-8}\,\text{C}$ fuera transportada desde $A(1, 2)$ hasta $B(2, -1)$.
c) La densidad de carga que produce este campo eléctrico.

### 4.- Teorema de Earnshaw
Demostrar que el potencial electrostático no puede tener un máximo o un mínimo locales en una región del espacio donde no haya cargas. Demostrar que un sistema estacionario de cargas no puede estar en equilibrio estable bajo su propia influencia (Teorema de Earnshaw).

### 5.- Superficie equipotencial cero de dos cargas
Hallar el potencial electrostático debido a dos cargas $q_1$ y $q_2$ situadas a una distancia $d$ una de la otra. Comprobar que la superficie equipotencial $V = 0$ es una esfera.

### 6.- Cavidad esférica en distribución uniforme
Una distribución de carga tiene una región en la cual la densidad de carga en volumen es uniforme. En esta zona se efectúa una cavidad esférica de radio $a$, extrayendo la carga original que allí se encontraba sin perturbar el resto de la distribución. Si la cavidad está centrada en un punto donde originalmente el valor del campo eléctrico era $\vec{E}_0$ y el del potencial $V_0$, calcular los nuevos valores de $\vec{E}$ y $V$ en ese punto. ¿En qué condiciones se puede realizar ese cálculo?

### 7.- Campo y carga de un potencial exponencial
La siguiente función escalar representa el potencial eléctrico en una zona vacía de materia:
$$V(x, y, z) = \begin{cases} V_0 e^{-ax} & \text{si } x > 0 \\ V_0 & \text{si } x \le 0 \end{cases}$$
donde $(x,y,z)$ son las coordenadas en el sistema cartesiano, y los parámetros $V_0$ y $a$ son conocidos. En la región de interés:
a) Obtener el campo eléctrico y verificar que se trata de un campo electrostático.
b) Determinar las distribuciones de carga que pueden dar lugar al potencial dado.

### 8.- Diferencias de potencial de dos cortezas cargadas y separadas
Una corteza esférica delgada, de radio $R_1$, está cargada con una distribución uniforme de carga $-Q_1$. Sobre otra corteza esférica delgada, de radio $R_2$, hay una distribución de carga total $+Q_2$, también uniforme. La distancia entre sus centros es $L$. Se pide:
a) Calcular la diferencia de potencial electrostático $V_{AB} = V_B - V_A$, tomando el punto $A$ como el centro de la segunda esfera y el punto $B$ sobre su superficie, en el exterior (en la línea que une ambos centros).
b) Encontrar $V_{CB} = V_C - V_B$, siendo la localización $C$ un punto a distancia $d$ del punto $B$, alineado con el punto $A$ y alejándose del punto $B$ en dirección opuesta a $A$.

---

## Hoja 5: Dipolos Eléctricos y Desarrollo Multipolar

### 1.- Aproximación dipolar en el eje Z
Supongamos dos cargas puntuales $+q$ y $-q$ situadas sobre el eje Z y separadas $2d$. Tomando como origen el punto medio, calcular:
a) Valor exacto del potencial para un punto del eje Z.
b) Valor mínimo de $z$ para poder aproximar el valor exacto del potencial por un término dipolar con un error inferior al 1%.
c) Repetir para el campo eléctrico.

### 2.- Desarrollo multipolar de sistemas de cargas discretas
Realizar el desarrollo multipolar (hasta el primer término no nulo) de los siguientes sistemas de cargas:
*(Nota: El archivo original indica dos figuras con cargas discretas en los vértices de un cuadrado/ejes de coordenadas).*

### 3.- Desarrollo multipolar de distribución superficial cuadrada
Hacer el desarrollo multipolar (hasta dipolo) de la siguiente distribución superficial de cargas: una placa cuadrada de lado $2a$ centrada en el origen con densidad superficial $\sigma_0$ constante en unas partes y opuesta en otras. Repetir con otras posiciones del origen de coordenadas.

### 4.- Momentos de carga y línea cargada
Calcular los momentos monopolar y dipolar de la distribución de carga de la figura, compuesta por:
* Una carga puntual $q_0$ a una distancia $b$ del origen sobre el eje Y.
* Un segmento de longitud $a$ que contiene una distribución de densidad lineal $\lambda = -q_0/a$, situado paralelo al eje X a una distancia $b$.

### 5.- Anillo con desarrollo multipolar
Dado un anillo de radio $a$ con densidad de carga $\lambda_0$ uniforme, calcular el potencial en cualquier punto con una aproximación desarrollando hasta el término cuadripolar.

### 6.- Anillo con densidad variable sinusoidal
Sobre una circunferencia de radio $a$ se distribuye una densidad lineal de carga que varía de la forma $\lambda = \lambda_0 \sin\theta'$, siendo $\lambda_0$ ($\text{C/m}$) constante. Calcular el potencial electrostático en cualquier punto hasta el término cuadripolar del correspondiente desarrollo multipolar.

### 7.- Varilla con densidad variable lineal
Dada una distribución lineal cuya densidad de carga viene dada por:
$$\lambda(z) = \frac{2\lambda_0 z}{L} \quad \text{para } -\frac{L}{2} \le z \le \frac{L}{2}$$
a) ¿Qué tipo de distribución es?
b) Calcular el potencial debido a esa distribución en puntos muy alejados.

---

## Hoja 6: Desarrollo Multipolar. Energía y Fuerza Electrostática

### 1.- Varilla con tres secciones de carga
Dada una distribución lineal:
$$\lambda(z) = \begin{cases} \lambda_0 & \text{si } -L \le z \le -L/2 \\ -\lambda_0 & \text{si } -L/2 \le z \le L/2 \\ \lambda_0 & \text{si } L/2 \le z \le L \end{cases}$$
a) ¿Qué tipo de distribución es?
b) Calcular el potencial debido a esa distribución en puntos muy alejados.

### 2.- Energía de cuatro cargas alineadas
Calcular la energía electrostática de una disposición de cuatro cargas puntuales $q, -q, q, -q$, alineadas y equidistantes una distancia $d$. Si desplazamos la tercera carga $d/2$ hacia la izquierda, manteniendo fijas las restantes cargas, ¿es más estable la nueva disposición?

### 3.- Autoenergía de esfera cargada
Una carga $q$ se encuentra distribuida en una esfera de radio $a$. Calcular la energía electrostática del sistema:
a) Si se distribuye en volumen (densidad uniforme $\rho_0$).
b) Si se distribuye en la superficie de la esfera (densidad superficial uniforme $\sigma_0$).

### 4.- Cargas en cuadrado y carga sobre eje Z
Cuatro cargas puntuales iguales $+q$ se encuentran en los vértices de un cuadrado de lado $d$ sobre el plano XY, centrado en el origen de coordenadas. Una quinta carga puntual $-q$ se coloca sobre el eje Z a una distancia $z$ del centro del cuadrado ($z \ll d$), de forma que estará a la misma distancia de cualquiera de las otras cargas.
Calcular la energía electrostática del sistema de cargas descrito. ¿Qué fuerza electrostática sufre la carga $-q$?

### 5.- Fuerza entre esfera y anillo coaxiales
Una corteza esférica de radio $b$ tiene una densidad de carga uniforme $\sigma_0$, y está situada coaxialmente a una distancia $z$ sobre un anillo cargado de radio $a$ con una densidad lineal de carga $\lambda_0$. Calcular la fuerza de interacción entre ambos objetos.

### 6.- Equilibrio de dos dipolos giratorios
Dos dipolos $\vec{p}_1$ y $\vec{p}_2$ se sitúan en posiciones fijas a lo largo del eje X, dejándose libertad para que ambos puedan girar respecto al eje Z. ¿Qué posición (o posiciones) relativa será la de equilibrio?

### 7.- Dipolo en volumen cargado
Dentro de un volumen de dimensiones $2a$, $2b$ y $2c$ ($b, c \gg a$) hay una distribución uniforme de carga, de densidad volúmica $\rho_0$. En un punto interior $(x, y, z)$ del plano $x = x_0$ ($|x_0| < a$), donde $|y| \ll b$ y $|z| \ll c$, se sitúa un dipolo eléctrico puntual $\vec{p}$. Calcular la fuerza eléctrica sobre el dipolo y el momento del par de giro si:
a) $\vec{p} = p_0 \vec{u}_x$
b) $\vec{p} = p_0 \vec{u}_y$


---

# Tema 2: Conductores y Sistemas de Conductores

## Hoja 1: Conductores en Equilibrio Electrostático

### 1.- Cargar canica de cobre al vacío
Calcular la energía necesaria para cargar una canica de cobre, de $1\,\text{cm}$ de radio, hasta el punto de "vaciarla" de cargas libres (suponiendo que se pudiera hacer tal cosa).
*Datos:* densidad del cobre $8960\,\text{kg/m}^3$, masa atómica $63.54\,\text{u}$, el cobre tiene un electrón libre por átomo.

### 2.- Carga puntual en corteza conductora
Una carga puntual $q$ se sitúa en el centro de una corteza esférica de material conductor de radios $a$ y $b$ ($a < b$). Calcular el campo eléctrico en todo el espacio suponiendo la carga total del conductor igual a $Q$.

### 3.- Dos cortezas concéntricas delgadas
Dados dos conductores esféricos concéntricos, huecos y de espesores despreciables, siendo el interior $C_1$ de radio $a$ y el exterior $C_2$ de radio $b$ ($a < b$), calcular el campo eléctrico y el potencial en cualquier punto del espacio, así como la carga y el potencial de cada conductor en las situaciones siguientes:
3.1.- $C_1$: carga $q_1$ y aislado; $C_2$: $q_2 = 0$ y aislado.
3.2.- $C_1$: carga $q_1$ y aislado; $C_2$: carga $q_2$ y aislado.
3.3.- $C_1$: $q_1 = 0$ y aislado; $C_2$: carga $q_2$ y aislado.
3.4.- $C_1$: potencial $V_1$; $C_2$: potencial $V_2 = 0$.
3.5.- $C_1$: potencial $V_1 = 0$; $C_2$: potencial $V_2$.
3.6.- $C_1$: carga $q_1$ y aislado; $C_2$: potencial $V_2 = 0$.

### 4.- Tres esferas concéntricas con una a tierra
Un dispositivo electrostático consta de tres esferas metálicas de radios $a$, $2a$ y $4a$, huecas, delgadas, dispuestas concéntricas en el vacío. La interior $C_1$ y la exterior $C_3$ poseen cargas $q_1$ y $q_3$, respectivamente, y $C_2$ se conecta a tierra ($V_2 = 0$). Calcular:
a) Densidades de carga en las superficies interna y externa de cada uno de los tres conductores. ¿Está cargada la esfera $C_2$ a tierra?
b) Campo y el potencial electrostático en cualquier punto.
c) Potencial de los conductores interior y exterior.
d) ¿Qué diferencia existiría en los resultados si el conductor $C_1$ fuese macizo (no hueco)?

### 5.- Variaciones del sistema de tres esferas
Supongamos inicialmente descargadas y aisladas las esferas del problema anterior:
5.1.- Se deposita una carga $Q$ sobre la esfera $C_2$. ¿Qué potencial deberá aplicarse a la esfera exterior $C_3$ para que $V_2 = 0$?
5.2.- Supongamos ahora que los conductores están conectados a tres fuentes de alimentación de potenciales $V_1$, $V_2$ y $V_3$. Calcular las cargas adquiridas por las tres esferas.
5.3.- A continuación, se desconectan las fuentes y, posteriormente, $C_2$ se une a tierra manteniéndose los otros dos conductores aislados. En esta nueva situación, calcular las cargas y los potenciales de los tres conductores. ¿Han variado las cargas de los conductores?
5.4.- Sin modificar la disposición entre los conductores, se procede entonces a cortocircuitar $C_1$ y $C_3$ mediante un hilo conductor que luego se retira. Si el conductor $C_2$ se ha mantenido conectado a tierra, ¿qué carga ha adquirido cada conductor? Calcular los potenciales $V_1$ y $V_3$.

### 6.- Tres placas conductoras paralelas
Se disponen en el vacío tres placas conductoras, iguales, paralelas, de área $S$, muy próximas a una pequeña distancia $d$. Sobre la placa 1 se deposita una carga de valor $Q$, sobre la 2 una carga de valor $-Q$, estando descargada la placa 3. Despreciando efectos de borde, estudiar el reparto de las cargas sobre cada cara de las placas. ¿Y si se cortocircuitan las placas 1 y 3? Repetir si colocamos cargas del mismo signo ($Q$) en las placas 1 y 2.

### 7.- Cuatro placas conductoras paralelas
Se disponen en el vacío cuatro placas conductoras, iguales, paralelas, de área $S$, muy próximas a una pequeña distancia $d$. Se cortocircuitan las placas 1 y 3 y las placas 2 y 4, se deposita una carga $Q$ en la placa 1, y una carga $-Q$ en la placa 4.
a) Despreciando efectos de borde, estudiar el reparto de las cargas sobre cada cara de las placas.
b) Calcular la capacidad total del sistema entre las placas 1 y 4.

---

## Hoja 2: Sistemas de Conductores, Condensadores, Energía y Fuerza

### 1.- Esferas conductoras lejanas con potencial y carga
Dos esferas conductoras, $A$ y $B$, de radios $a$ y $b$, respectivamente, se encuentran separadas por una distancia $d$ entre sus centros muy grande en comparación con sus radios. La esfera $A$ está conectada a una fuente $V_0$, mientras que $B$ se halla aislada y posee una carga $q$. Calcular la carga que adquiere $A$ y el potencial que alcanza $B$.

### 2.- Esferas conductoras cortocircuitadas
Las mismas esferas del problema anterior se cortocircuitan mediante un cable muy largo y se cargan con una carga $Q$. Calcular el potencial y carga que adquiere cada esfera cuando llegan al equilibrio electrostático. ¿Qué sucede si una es mucho más grande que la otra?

### 3.- Prismas conductores en cascada
Cuatro prismas conductores se disponen de forma paralela y concéntrica con separaciones, donde $a = d = 1\,\text{cm}$, $b = 2\,\text{cm}$ y $c = 3\,\text{cm}$. La separación entre placas es de $e = 2\,\text{cm}$. Calcular la capacidad del sistema entre las placas 1 y 4, despreciando efectos de borde.

### 4.- Capacidad de cilindros concéntricos
Calcular la capacidad de un condensador compuesto por dos cilindros conductores concéntricos, de radios $a$ y $b$ y longitud $L \gg a, b$.

### 5.- Esfera interna a tierra y corteza cargada
Un conductor esférico de radio $a$, conectado a tierra, se halla rodeado por una corteza esférica conductora, concéntrica con él, de radios interior $b$ y exterior $c$ ($a < b < c$), que posee una carga $q$. Calcular la energía electrostática almacenada por dicho sistema de conductores.

### 6.- Disminución de energía al cortocircuitar
Dos esferas conductoras, huecas, delgadas, concéntricas, de radios $a$ y $b$ ($a < b$), poseen respectivamente cargas $q_1$ y $q_2$. Demostrar que, si se cortocircuitan, el sistema evoluciona a un estado de menor energía y razonar "dónde se ha ido" la diferencia de energía.

### 7.- Fuerza sobre placas a voltaje constante
¿Qué fuerza electrostática aparece entre las armaduras de un condensador plano-paralelo, de área $S$ y separación $d$, al mantenerlo conectado a una fuente de potencial $V_0$?

### 8.- Condensador cargado y placas separadas
Un condensador plano-paralelo, de área $1\,\text{cm}^2$ y espesor $1\,\text{cm}$, se carga a una d.d.p. $V_0 = 10^3\,\text{V}$. Calcular la energía electrostática almacenada. Seguidamente se desconecta la fuente $V_0$ y se separan las placas hasta la distancia final de $2\,\text{cm}$, ¿qué d.d.p. existirá ahora entre las placas? ¿Qué energía electrostática ha sido necesaria para realizar el proceso?

### 9.- Conexión en paralelo y balance de energía
Un condensador de $20\,\text{pF}$ se carga hasta $3\,\text{kV}$, seguidamente, se desconecta de la fuente y se conecta en paralelo con otro condensador inicialmente descargado de $50\,\text{pF}$. ¿Qué carga adquiere cada uno de los condensadores? Calcular la energía inicial almacenada en el primer condensador y la energía final almacenada en los dos condensadores. ¿Se pierde o se gana energía al conectar los condensadores? Razonar el balance de energía.

### 10.- Condensador con lámina intermedia
Entre las placas de un condensador plano-paralelo, de área $S$ y separación $d$, se inserta una lámina metálica de espesor $t$ y área $S$.
a) Demostrar que la capacidad del sistema resultante viene dada por $C = \frac{\varepsilon_0 S}{d - t}$, independiente de la posición de la lámina de metal.
b) El condensador se carga con una carga $q$ y se desconecta de la fuente. Calcular la fuerza ejercida sobre la lámina, así como la fuerza de atracción entre cada una de las placas y la lámina.

### 11.- Esfera con dos cavidades concéntricas
En una esfera metálica de radio $4a$ se han hecho dos cavidades, también esféricas, de radio $2a$ cada una. Concéntricas con cada una de estos huecos se hallan sendas esferas metálicas de radio $a$. No hay más conductores en el sistema.
La esfera exterior se encuentra aislada y descargada; una de las esferas interiores se encuentra a un potencial $V_1$ y la otra se encuentra a tierra ($0\,\text{V}$).
a) ¿Cuál es la carga en cada conductor? ¿Y el potencial?
b) Hallar la energía almacenada en el sistema.

### 12.- Hemisferios conductores pesados
Una esfera conductora de radio $a$ está formada por dos piezas iguales separadas por un plano ecuatorial horizontal. El hemisferio superior descansa libremente sobre el inferior por la acción de su peso. La esfera está caracterizada por una densidad másica $\rho_m$. Calcular el potencial máximo que se puede aplicar a dicha esfera para que el hemisferio superior permanezca en reposo.


---

# Tema 3: Medios Dieléctricos

## Hoja 1: Medios Dieléctricos. Polarización Permanente

### 1.- Cilindro uniformemente polarizado
Un cilindro dieléctrico de radio $a$ y longitud $L$ está uniformemente polarizado en dirección de su eje. Suponiendo conocido el vector polarización $\vec{P}$, obtener el campo eléctrico en puntos del eje. Describir cualitativamente cómo serán fuera del mismo las líneas del campo eléctrico y del vector desplazamiento.

### 2.- Lámina uniformemente polarizada
Dada una lámina dieléctrica infinita de espesor $d$ con polarización transversal uniforme conocida, calcular el campo eléctrico en cualquier punto del espacio.

### 3.- Esfera con polarización permanente
Una esfera dieléctrica de radio $a$, centrada en el origen de coordenadas, posee una polarización permanente $\vec{P} = P \vec{u}_x$. Calcular el campo eléctrico y el vector desplazamiento en el centro de la esfera en los casos ($P_0 = \text{cte.}$):
a) $P = P_0$
b) $P = P_0 \frac{x}{a}$

### 4.- Carga de polarización de un cubo
Calcular las densidades de carga de polarización en un cubo dieléctrico de lado $L$ que posee una polarización permanente $\vec{P} = A \vec{r}$ ($A = \text{cte.}$), siendo el origen de coordenadas el centro del cubo.

### 5.- Cortezas conductoras con dieléctrico no lineal
Disponemos de dos conductores esféricos delgados, de radios $a$ y $4a$ respectivamente, concéntricos y descargados. Se coloca en el espacio intermedio una corteza esférica, de radios interior $a$ y exterior $2a$, de material no lineal con polarización:
$$\vec{P} = \frac{A}{r^2}\vec{u}_r$$
donde $A$ es una constante y $r$ la distancia al centro. Si además se cortocircuitan los dos conductores, determinar:
a) El vector desplazamiento y el campo eléctrico entre los dos conductores.
b) Las densidades de carga, especificando su naturaleza ("verdadera" o de polarización).

### 6.- Electrete cilíndrico coaxial
Dos conductores cilíndricos, delgados, coaxiales, de gran longitud $L$ y radios $a$ y $b$ ($a < b$), poseen cargas $q$ y $-q$, respectivamente. En la región comprendida entre ambos se introduce un electrete con polarización radial uniforme:
$$\vec{P} = P_0 \vec{u}_r$$
que ocupa todo el espacio ($P_0 = \text{cte.}$). Calcular, despreciando los efectos de borde, $\vec{E}$ y $\vec{D}$ en cualquier punto del espacio y la diferencia de potencial entre los conductores.

### 7.- Polarización no lineal azimutal
Se dispone de dos conductores cilíndricos, coaxiales, de espesores despreciables, longitud $L$ y radios $a$ y $b$, respectivamente ($L \gg b \gg a$). En el espacio intermedio se coloca una pieza material cilíndrica, coaxial con los conductores, de longitud $L$, radio interior $c$ y exterior $b$ ($a < c < b$) de un material no lineal con una polarización dada por:
$$\vec{P} = \frac{P_0}{r}\vec{u}_\phi$$
siendo $P_0$ una constante y $r$ la distancia de cualquier punto al eje. Si depositamos una carga $Q$ en el conductor interior y conectamos el exterior a tierra, determinar:
a) El campo eléctrico y el vector desplazamiento en cualquier punto del espacio. Representar la distribución de líneas de campo en ambos casos.
b) Las densidades de carga ("verdaderas" o de polarización) que aparecen en el sistema.

### 8.- Placas paralelas con electrete parcial
Entre dos placas conductoras, de sección $A$ y separación $d$, que se encuentran cortocircuitadas se coloca, pegada a una de ellas, una lámina de material no lineal, de sección $A$ y espesor $h$ ($h < d$), que presenta una polarización uniforme $\vec{P}$ normal a las placas. Despreciando los efectos de borde, determinar:
a) Vector desplazamiento y campo eléctrico entre las dos placas conductoras.
b) Densidades de carga existentes.

---

## Hoja 2: Medios Dieléctricos. Medios Lineales

### 1.- Esfera dieléctrica con carga puntual central
Calcular el campo electrostático debido a una carga puntual $q$ situada en el centro de una esfera dieléctrica de radio $a$ y permitividad $\varepsilon$. Calcular también las cargas de polarización en el medio.

### 2.- Esfera dieléctrica con carga volumétrica radial
En una bola de material dieléctrico de permitividad $\varepsilon$ y radio $a$, existe una distribución de carga de densidad dada por:
$$\rho(r) = A r$$
siendo $A$ ($\text{C/m}^4$) una constante y $r$ la distancia al centro de simetría. Calcular:
a) El vector desplazamiento, el campo eléctrico y el potencial electrostático en cualquier punto.
b) Las cargas de polarización.

### 3.- Carga puntual en medio con permitividad variable
La permitividad de un medio dieléctrico ilimitado es función de la distancia al centro $r$ de simetría de la forma:
$$\varepsilon(r) = \varepsilon_0 \left(1 + \frac{a}{r}\right) \quad (a = \text{cte.})$$
Una carga puntual de valor $q$ se sitúa en $r = 0$. Calcular:
a) El vector desplazamiento, el campo eléctrico y el potencial en cualquier punto.
b) Las cargas de polarización.

### 4.- Esfera conductora semisumergida
Una esfera conductora de radio $a$ y carga $q$, flota sumergida a la mitad en un líquido dieléctrico de permitividad $\varepsilon$.
a) Calcular el campo eléctrico en todo el espacio.
b) Obtener la distribución de la carga sobre la esfera conductora.

### 5.- Cilindros concéntricos semisumergidos verticalmente
Consideremos dos conductores cilíndricos coaxiales, delgados, de gran longitud $L$, y radios medios $a$ y $2a$. Inicialmente se conectan a una batería que suministra una diferencia de potencial $V_0$ entre ellos y que posteriormente se desconecta, manteniéndose los conductores aislados.
Si se colocan verticalmente y se llena el espacio entre los conductores con líquido dieléctrico de permitividad $\varepsilon$, justo hasta la mitad de su volumen, ¿cuál será ahora la diferencia de potencial?

### 6.- Cilindros concéntricos semisumergidos horizontalmente
Si partiendo del problema nº 5, se giran los conductores conteniendo el líquido dieléctrico hasta colocarlos horizontalmente, ¿cuál será la diferencia de potencial entre los conductores en esta situación?

### 7.- Tres placas con carga y dieléctrico
Sean tres placas metálicas, descargadas, paralelas, de área $S$, muy próximas entre sí a distancias $d_1$ y $d_2$. Entre las dos primeras existe una distribución de carga de densidad volúmica $\rho$ uniforme, siendo en esta zona la permitividad próxima a la del vacío. En la otra región se introduce un dieléctrico de permitividad $\varepsilon$. Se pide:
a) La densidad de carga en las superficies de cada placa.
b) El campo electrostático y el potencial en ambas regiones.

---

## Hoja 3: Condensadores. Energía y Fuerzas Electrostáticas

### 1.- Ruptura dieléctrica en condensadores rellenos
Dados dos condensadores plano-paralelos iguales, de área $A$ y espesor $d$, se procede a rellenar el espacio entre placas con dos materiales, de permitividades $\varepsilon_1$ y $\varepsilon_2$, según la geometría de las figuras (en una figura se dividen longitudinalmente en paralelo a las placas, y en otra se dividen transversalmente en paralelo al campo; suponer que cada material ocupa la mitad del volumen en ambos casos).
Los dos condensadores se conectan a sendas fuentes de igual voltaje $V_0$. Si el campo de ruptura es de igual valor en estos medios y consideramos instantáneo el fenómeno de ruptura dieléctrica, ¿qué condensador podrá soportar mayor voltaje aplicado sin perforarse?

### 2.- Condensador con dieléctrico linealmente variable
Un condensador plano-paralelo de área $S$ y separación entre placas $d$, contiene un medio estratificado que lo llena completamente, de permitividad dada por la expresión $\varepsilon(x) = \varepsilon_0 \left(1 + \frac{3x}{d}\right)$, siendo $x = 0$ el plano que contiene una de las placas. Calcular la capacidad de este condensador y las densidades de carga de polarización en el dieléctrico cuando el condensador está cargado con una carga $q$.

### 3.- Placas inclinadas o medio con variación lateral
Un condensador plano-paralelo está formado por dos placas cuadradas de lado $a$ y separadas una distancia $d$ ($d \ll a$), y contiene un medio estratificado que lo llena completamente, de permitividad dada por la expresión $\varepsilon(x) = \varepsilon_0 \left(1 + \frac{3x}{a}\right)$ (siendo $x$ la coordenada a lo largo del lado de la placa). Si se carga con una diferencia de potencial $V$, calcular:
a) La densidad de carga superficial en las placas conductoras.
b) Las densidades de carga de polarización en el dieléctrico.
c) La capacidad de ese condensador.
d) Las fuerzas que aparecen sobre las placas del condensador.

### 4.- Introducción parcial de dieléctrico y ascensión de líquido
Un condensador plano-paralelo, de área $S$ y separación $d$, se carga con una carga $q$. Entre sus placas se introduce parcialmente una lámina dieléctrica de permitividad $\varepsilon$ y espesor $d$. ¿Qué fuerza aparece sobre esta lámina?
*Aplicación:* El condensador se conecta a una batería $V_0$ y se coloca verticalmente sobre un recipiente que contiene un líquido dieléctrico de permitividad $\varepsilon$ y densidad másica $\rho_m$. ¿Hasta qué altura ascenderá el líquido por el interior del condensador?

### 5.- Dispositivo de elevación electrostática
En algunas aplicaciones industriales se utilizan campos eléctricos para levantar pequeños objetos. Para ello es posible utilizar un dispositivo formado por dos láminas metálicas (1 y 2), cuadradas de lado $L$, conectadas a una fuente de potencial $V_0$. Una tercera lámina metálica, aislada y descargada, paralela a ellas y de igual anchura $L$, completa el sistema y constituye el objeto a levantar.
Las tres láminas son de espesor despreciable y entre ellas hay un gas dieléctrico de permitividad $\varepsilon$. Suponiendo que los efectos de borde pueden despreciarse ($d \ll L$), calcular la fuerza electrostática que tiende a levantar el objeto.


---

# Tema 4: Teoría del Potencial

## Hoja 1: Teoría del Potencial

### 1.- Condensador con dos capas utilizando ecuación de Laplace
Las placas de un condensador plano, de área $S$ y separación $d$, se conectan una a tierra y otra a una fuente $V_0$. Se introducen entre las placas dos láminas dieléctricas de permitividades $\varepsilon_1$ y $\varepsilon_2$, área $S$ y espesores $d_1$ y $d_2$ (siendo $d_1 + d_2 = d$). Utilizando la ecuación de Laplace para hallar la función potencial, calcular la capacidad del condensador resultante.

### 2.- Potencial de esfera con carga volumétrica uniforme
Calcular la función potencial debida a una distribución de carga esférica en volumen, de radio $R$ y densidad uniforme $\rho_0$.

### 3.- Esfera conductora en campo uniforme
Hallar el potencial cuando en una región, en la que inicialmente había un campo electrostático uniforme $\vec{E}_0$, se introduce una esfera conductora descargada de radio $a$.

### 4.- Esfera dieléctrica en campo uniforme
Repetir el problema 3 si sustituimos la esfera conductora por una dieléctrica de permitividad $\varepsilon$.

### 5.- Cavidad hueca en dieléctrico en campo uniforme
En una región del espacio, de permitividad $\varepsilon$, existe un campo electrostático uniforme $\vec{E}_0$, si en esa región hay una cavidad hueca de radio $a$, calcular el valor del campo eléctrico en el centro de esa cavidad.

### 6.- Cilindro conductor en campo uniforme
Hallar el potencial cuando en una región, en la que inicialmente había un campo electrostático uniforme $\vec{E}_0$, se introduce un cilindro conductor descargado de radio $a$ y muy largo cuyo eje es perpendicular a dicho campo.

### 7.- Carga entre planos en ángulo recto (Método de Imágenes)
Dos conductores planos, conectados a tierra, forman entre sí un ángulo $\pi/2$. En la bisectriz, a una distancia $d$ de cada plano, se coloca una carga $q$. ¿A qué distribución de cargas equivale? Repetir si el ángulo que forman los conductores es $\pi/4$.

### 8.- Carga puntual frente a esfera conductora
Un sistema aislado está compuesto por una esfera metálica de radio $a$ y una carga puntual $q$ situada a una distancia $d$ de su centro. Calcular la fuerza que aparece sobre dicha carga en los casos siguientes:
1) La esfera conductora está conectada a tierra y $d > a$.
2) La esfera está aislada y descargada, y $d > a$.
3) El conductor posee una carga total $Q$.
4) El conductor se conecta a un potencial $V_0$.
5) La esfera conductora está conectada a tierra y $d < a$ (carga en el interior).

### 9.- Órbita estable alrededor de esfera a tierra
Un sistema aislado está compuesto por una esfera metálica de radio $a$ unida a tierra y una carga puntual $q$, de masa $m$, que gira con velocidad $v$ (que supondremos pequeña) sobre una órbita de radio $2a$. Calcular el valor de $v$ para que la órbita permanezca estable.

### 10.- Plano conductor con saliente semiesférico
Consideremos un plano conductor que posee un saliente semiesférico de radio $a$. Calcular la fuerza que aparece sobre una carga puntual situada en el eje perpendicular al plano de dicho saliente a una distancia $d$, tal como muestra la figura.

### 11.- Imágenes de un dipolo
Obtener la imagen de un dipolo sobre una superficie plana y otra esférica.


---

# Tema 5: Corriente Estacionaria

## Hoja 1: Corriente Estacionaria

### 1.- Cilindro cargado giratorio
Un cuerpo cilíndrico, de radio $a$ y longitud $L$, cargado con densidad uniforme $\rho$, gira con velocidad angular constante $\omega$ respecto al eje de simetría. Calcular la corriente que atravesará un cuadrado de lado $b$ ($b > a$) que apoya uno de sus lados sobre el eje de rotación.

### 2.- Electrodo semiesférico con líquido conductor
El espacio entre un electrodo (conductor perfecto) esférico de radio $a$ y otro semiesférico delgado de radio $b$ ($a < b$), ambos concéntricos, se llena con un líquido de conductividad $\gamma$. Calcular la resistencia de dicho líquido.

### 3.- Electrodos esféricos con conductividad radial variable
El espacio comprendido entre dos electrodos esféricos concéntricos, de radios $a$ y $b$, está ocupado por un material de conductividad:
$$\gamma(r) = \frac{\gamma_0 b}{r}$$
siendo $\gamma_0$ (S/m) un parámetro conocido.
a) Calcular la resistencia que presenta dicho material.
b) Calcular la densidad de carga en el interior del material.

### 4.- Condensador circular con material radialmente no homogéneo
Se dispone de un condensador de placas plano-paralelas, circulares, de radio $a$ y distancia $d$ entre placas ($d^2 \ll \pi a^2$). En el interior se coloca un material no homogéneo, cuyas propiedades dependen de la distancia $r$ al eje del condensador, siendo su permitividad $\varepsilon = \varepsilon_0 \left(1 + \frac{r}{a}\right)$ y su conductividad $\gamma = \gamma_0 \left(2 - \frac{r}{a}\right)$. Si se conectan sus extremos a una batería que proporciona una diferencia de potencial $V_0$, calcular:
a) El valor del campo eléctrico, vector desplazamiento y densidad de corriente en el espacio entre las dos placas.
b) Las densidades de carga en los electrodos (placas).
c) La resistencia y la capacidad de ese condensador.

### 5.- Placas paralelas con dos capas conductoras
Dos placas conductoras iguales de área $S$, paralelas y muy próximas a una distancia $d$, están conectadas a potenciales $V_1$ y $V_2$. El espacio entre ellas se llena con dos láminas, de espesores $a$ y $b$ ($a + b = d$), caracterizadas por $\varepsilon_1, \gamma_1$ y $\varepsilon_2, \gamma_2$. Calcular el potencial y la densidad de carga en la superficie de separación, y obtener la resistencia entre placas. Estudiar la dependencia en función de $V_1$ y $V_2$, ¿qué sucede si las láminas están "en paralelo"?

### 6.- Pieza de geometría irregular
Una pieza con geometría cónica truncada o sectorial está compuesta por un material conductor, de conductividad $\gamma$ y permitividad $\varepsilon$. Si se conecta a dos electrodos, calcular su resistencia y capacidad internas.

### 7.- Corriente de fugas en cable coaxial
Las corrientes de fugas se producen cuando el dieléctrico que separa dos conductores posee una conductividad no nula, de forma que una pequeña corriente fluye a través del material. Consideremos un cable coaxial constituido por dos conductores cilíndricos coaxiales de radios $a$ y $b$ ($a < b$) y gran longitud $L$, entre los que se aplica una tensión $V_0$. Admitiendo que el espacio intermedio posee una cierta conductividad $\gamma$ (mucho menor que la de los conductores coaxiales), ¿qué corriente de fugas $I_f$ aparece?

### 8.- Corriente de fugas con dos capas en coaxial
El dieléctrico del cable coaxial anterior está formado por dos capas cilíndricas coaxiales de materiales caracterizados por $\varepsilon_1, \gamma_1$ y $\varepsilon_2, \gamma_2$ y superficie de separación de radio $c$ ($a < c < b$). Si fluye una corriente $I_f$ desde el conductor interior al exterior, determinar:
a) El vector densidad de corriente y el campo eléctrico en $a < r < b$.
b) La diferencia de potencial aplicada entre los dos conductores.
c) La resistencia del dispositivo y la potencia disipada.
d) Las densidades de carga eléctrica sobre los conductores.
e) El potencial y la carga en $r = c$.

### 9.- Cono truncado de material conductor
Dado un cono truncado, de radios de las bases $a$ y $b$, y altura $h$, de material de conductividad $\gamma$, estimar la resistencia que presenta entre sus bases (aproximación si $h \gg |b - a|$).


---

# Tema 6: Campo de Inducción Magnética y Ley de Ampère

## Hoja 1: Campo de Inducción Magnética

### 1.- Campo en el centro de espira cuadrada
Un circuito tiene la forma de un cuadrado de lado $a$ y está recorrido por una corriente $I$. Calcular el campo de inducción magnética $\vec{B}$ en el centro del cuadrado.

### 2.- Campo en el centro de polígono regular
Un circuito tiene forma de polígono regular de $N$ lados de dimensión $a$, y está recorrido por una corriente $I$. Calcular $\vec{B}$ en el centro del mismo.

### 3.- Disco giratorio (Experimento de Rowland)
Un disco de radio $a$ con densidad de carga uniforme $\sigma$ gira en torno a su eje perpendicular con velocidad angular constante $\omega$ (experimento de Rowland). ¿Cuál será el valor del campo $\vec{B}$ en puntos del eje de rotación?

### 4.- Eje de un solenoide de longitud finita
Un solenoide está constituido por un arrollamiento de $N$ espiras circulares de radio $a$ y longitud $L$. Si se hace circular una corriente $I$, ¿qué valor tiene $\vec{B}$ en puntos del eje?

### 5.- Plano bisector de lámina conductora plana
Calcular el campo $\vec{B}$ en el plano bisector de una lámina conductora de anchura $2d$, espesor despreciable y longitud infinita, por la que circula una corriente superficial de densidad $\vec{K}$.

### 6.- Esfera cargada giratoria
Un conductor esférico de radio $a$ y densidad superficial de carga uniforme $\sigma$, se hace girar en torno a uno de sus diámetros a una velocidad angular constante $\omega$. Calcular $\vec{B}$ en el centro de la esfera.

### 7.- Dos hemisferios giratorios en sentido opuesto
Una esfera de radio $a$ tiene una carga $Q$ uniformemente distribuida sobre su superficie. El hemisferio superior gira en torno a su eje de simetría con una velocidad angular constante $\omega_1$, mientras que el inferior gira en sentido contrario con velocidad angular $\omega_2$, también constante ($\omega_1 \neq \omega_2$). Calcular el campo de inducción magnética $\vec{B}$ en el centro de la esfera. ¿Qué parte de la carga total $Q$ es necesario distribuir en cada hemisferio para que $B$ sea nulo en dicho punto?

### 8.- Semicilindro infinito con densidad de corriente axial variable
Por la superficie semicilíndrica de la figura, de gran longitud y radio $a$, circula una corriente eléctrica de densidad:
$$\vec{K} = K_0 \cos\theta \vec{u}_z$$
siendo $K_0$ una constante (A/m), $\theta$ el ángulo definido por el vector radial en coordenadas cilíndricas y el eje x, y $\vec{u}_z$ el vector unitario en la dirección axial.
a) Determinar el campo de inducción magnética $\vec{B}$ en cualquier punto del eje del sistema.
b) Si en dicho eje se coloca un hilo rectilíneo muy largo por el que circula una corriente eléctrica en dirección axial de valor $I$, calcular la fuerza por unidad de longitud entre ambos sistemas.

### 9.- Parámetros para campo magnético válido
En un sistema de coordenadas cartesiano, un cierto campo viene expresado por:
$$\vec{B} = ax\vec{u}_x - yz\vec{u}_y + bxz\vec{u}_z$$
a) Determinar el valor de los parámetros $a$ y $b$ (supuestos constantes) para que pueda corresponder a un campo de inducción magnética.
b) Obtener la densidad de corriente eléctrica que genera ese campo.

---

## Hoja 2: Ley de Ampère. Superposición. Potencial Vector Magnético

### 1.- Hilo indefinido mediante Ampère
Utilizando el teorema de Ampère, calcular el campo de inducción magnética $\vec{B}$ que genera un hilo indefinido de corriente $I$.

### 2.- Conductor cilíndrico macizo
Obtener el campo $\vec{B}$ debido a un conductor cilíndrico infinito de sección circular de radio $a$ que transporta una corriente $I$ uniforme en su sección.

### 3.- Capa cilíndrica conductora
Una capa cilíndrica conductora, de radios interior $a$ y exterior $b$, muy larga, transporta longitudinalmente una corriente $I$ distribuida uniformemente en su volumen. Calcular el campo $\vec{B}$ en cualquier punto.

### 4.- Cable coaxial con corrientes opuestas
Un cable coaxial infinito está constituido por dos conductores cilíndricos: el interior de radio $a$, el exterior es una capa cilíndrica de radios $b$ y $c$ ($a < b < c$). Si el cable transporta una corriente $I$ en sentidos opuestos en ambos conductores, ¿qué valor tiene el campo $\vec{B}$ en cualquier punto?

### 5.- Cilindro con densidad de corriente variable
Por un cilindro, de gran longitud y radio $a$, circula una corriente con densidad no uniforme, en una dirección paralela al eje Z y de valor:
$$\vec{J}(r) = J_0 \left( 2 - \frac{3}{2}\frac{r}{a} \right) \vec{u}_z$$
siendo $J_0$ una constante y $r$ la distancia al eje de simetría. Determinar la intensidad del campo $\vec{B}$ en cualquier punto del espacio.

### 6.- Corriente azimutal sobre cilindro
Dada una distribución de corriente superficial de densidad $\vec{K} = K \vec{u}_\phi$ ($K = \text{cte.}$) sobre un cilindro de radio $a$ y muy largo, determinar el campo de inducción magnética $\vec{B}$ en puntos fuera del eje.

### 7.- Placa de espesor finito
Un conductor plano, muy largo, muy ancho y de espesor $2d$, transporta una corriente de densidad $\vec{J}$ uniforme. Calcular el campo $\vec{B}$ en cualquier punto.

### 8.- Toroide de sección rectangular
Sobre un anillo toroidal, de radios interior $a$ y exterior $b$, y altura $h$, se enrollan $N$ espiras por las que se hace circular una corriente $I$. Calcular el campo de inducción magnética $\vec{B}$.

### 9.- Solenoide helicoidal real
Calcular el campo magnético $\vec{B}$ en cualquier punto del espacio debido al arrollamiento helicoidal de un solenoide, de radio $a$ y gran longitud, teniendo en cuenta que la dirección de la corriente forma un ángulo $\alpha$ con el plano perpendicular al eje de revolución, el eje Z, pudiéndose modelar con una densidad superficial en coordenadas cilíndricas:
$$\vec{K}_s = K_s (\cos\alpha \vec{u}_\phi + \sin\alpha \vec{u}_z)$$
siendo $K_s$ (A/m) constante.

### 10.- Cavidad cilíndrica excéntrica
En el espacio comprendido entre dos cilindros conductores no coaxiales (es decir, con una cavidad cilíndrica paralela descentrada) circula una corriente longitudinal de densidad $\vec{J}$ uniforme. Obtener el campo $\vec{B}$ en la cavidad del conductor interior.

### 11.- Potencial vector de un segmento
Un segmento de corriente $I$ de longitud $2L$ se sitúa sobre el eje Z centrado en el origen de coordenadas. Determinar el potencial vector $\vec{A}$ en puntos del plano XY.

### 12.- Potencial vector de un cilindro infinito
Calcular el potencial vector $\vec{A}$ en cualquier punto para un cilindro infinito de radio $a$ que transporta una densidad de corriente $\vec{J}$ uniforme.

### 13.- Potencial vector de espira circular
Dada una espira circular de radio $a$ por la que se hace circular una corriente $I$, obtener el potencial vector $\vec{A}$ en puntos del eje y determinar un valor aproximado en cualquier punto del espacio alejado de la espira (aproximación dipolar).

### 14.- Potencial vector de solenoide infinito
Sea un solenoide cilíndrico infinito de radio $a$ con $n$ espiras por unidad de longitud por las que se hace circular una corriente $I$. Hallar el potencial vector $\vec{A}$.

### 15.- Potencial vector de dos planos paralelos
Sobre dos planos paralelos infinitos, separados una distancia $d$, circulan sendas corrientes superficiales de densidades $\vec{K}$ y $-\vec{K}$, es decir, en sentidos contrarios. Calcular el potencial vector $\vec{A}$ en cualquier punto.


---

# Tema 7: Inducción Electromagnética y Fuerzas Magnéticas

## Hoja 1: Inducción Electromagnética: Ley de Lenz-Faraday

### 1.- Espira circular en campo variable
La dirección de un campo de inducción magnética uniforme es perpendicular al plano de una espira circular de $5\,\text{cm}$ de radio, $0.4\,\Omega$ de resistencia y autoinducción despreciable. Si el campo $\vec{B}$ no varía de dirección pero aumenta a razón de $40\,\text{mT/s}$, ¿qué fuerza electromotriz inducida aparece en la espira? ¿Y qué valor tiene la corriente que se induce?

### 2.- Esfera bobinada en campo armónico
Un hilo conductor se enrolla formando una esfera de radio $a$ con un número de vueltas por unidad de longitud $n = n_0 \sin\theta$, donde $\theta$ es el ángulo polar en coordenadas esféricas. Calcular la f.e.m. inducida cuando el dispositivo se introduce en un campo magnético armónico de frecuencia angular $\omega$, dirección $\theta = 0$ (eje Z) y amplitud $B_0$.

### 3.- Dos arrollamientos sobre toroide
Sobre un anillo toroidal, de radios interior $a$ y exterior $b$, y altura $h$, se disponen dos arrollamientos, sin contacto entre ellos y de diferente número de vueltas $N_1$ y $N_2$. Si circula una corriente variable $I(t)$ sobre el primero, ¿qué f.e.m. inducida aparece en el segundo?

### 4.- Bucle rectangular alejándose de hilo infinito
Un hilo rectilíneo muy largo, que transporta una corriente $I$, y un bucle rectangular, de lados $a$ y $b$, se encuentran situados en un mismo plano a una distancia inicial $d_0$. Si el bucle se aleja del hilo con velocidad constante $\vec{v}_0$ perpendicular al hilo, obtener la f.e.m. inducida.

### 5.- Bucle rectangular penetrando en campo magnético
Un circuito tiene forma rectangular, de lados $a$ y $b$, tiene una resistencia $R$ y una masa $m$, y se mueve con una velocidad inicial $\vec{v} = v_0 \vec{u}_x$ cuando penetra en una región de campo magnético uniforme $\vec{B} = B_0 \vec{u}_y$ (que ocupa el semiplano $x > 0$). Calcular el valor mínimo de $v_0$ necesario para que nuestro circuito penetre completamente en esa región.

### 6.- Varilla deslizante con impulso inicial
Dos hilos conductores semiinfinitos paralelos se sitúan a una distancia $\ell$ y sus extremos se unen mediante una resistencia $R$. Apoyada sobre estos hilos, se coloca una varilla metálica de longitud ligeramente mayor que $\ell$, masa $m$ y espesor despreciable. El circuito resultante se dispone en una región de campo magnético uniforme $B$ perpendicular al plano del circuito. Si se le comunica a la varilla un impulso de forma que comienza a moverse con velocidad $v_0$, ¿qué velocidad adquiere con el tiempo?

### 7.- Conductor recto en movimiento
Un conductor recto, de longitud $\ell$ y paralelo al eje Z, se mueve con velocidad constante $\vec{v} = v_0 \vec{u}_x$, atravesando una zona de campo magnético uniforme $\vec{B} = B_0 \vec{u}_y$. Calcular la f.e.m. inducida en la barra conductora, así como su polaridad.

### 8.- Disco de Faraday
Un disco de radio $a$ gira alrededor de su eje con velocidad angular constante $\omega$ en una región del espacio en la que existe un campo uniforme $\vec{B}$ paralelo al vector velocidad angular. Determinar la f.e.m. a lo largo de un camino cerrado que incluya un radio del disco (utilizando contactos deslizantes en el centro y en la periferia).

### 9.- Varilla giratoria en un extremo
Una varilla conductora, de longitud $a$, gira con respecto a un eje perpendicular que pasa por uno de sus extremos con velocidad angular constante $\omega$. Suponiendo que se halla inmersa en un campo estacionario y uniforme $\vec{B}$ paralelo al eje de rotación, calcular la f.e.m. inducida.

### 10.- Bucle rectangular en campo variable espacial y temporalmente
En una región del espacio en la que existe una inducción magnética:
$$\vec{B} = B_0 \cos(Ax) \sin(\omega t) \vec{u}_z$$
se coloca un bucle de corriente rectangular, de lados $a$ y $b$ paralelos a los ejes X e Y, que se desplaza con velocidad constante $\vec{v} = v_0 \vec{u}_x$. Suponiendo que ese bucle posee una resistencia $R$, calcular la f.e.m. inducida en el mismo, y determinar el valor y el sentido de la corriente inducida en un período.

### 11.- Bucle concéntrico con solenoide
Un bucle de corriente circular de radio $a$, resistencia $R$ y autoinducción $L$, se sitúa coaxial con un solenoide largo de $n$ espiras por unidad de longitud y radio $b$ recorridas por una corriente alterna de amplitud $I_0$ y frecuencia angular $\omega$.
Determinar la f.e.m. inducida en el bucle y la corriente que circulará por el mismo en los casos:
a) $a < b$ (bucle dentro del solenoide)
b) $a > b$ (bucle rodea al solenoide)

### 12.- Bucle giratorio dentro de solenoide
Un bucle de corriente circular de radio $a$ se sitúa de forma coaxial en el interior de un solenoide largo de $n$ espiras por unidad de longitud y radio $b$ ($b > a$), recorridas por una corriente $I = I_0 \sin(\omega t)$. Suponiendo que el bucle se hace girar con velocidad angular $\omega$ respecto a un eje que pasa por uno de sus diámetros, determinar la f.e.m. inducida.

---

## Hoja 2: Coeficientes de Autoinducción e Inducción Mutua. Momento Dipolar Magnético. Energía

### 1.- Autoinducción de solenoide recto
Calcular el coeficiente de autoinducción de un solenoide recto de $N$ espiras, longitud $\ell$ y radio $a$.

### 2.- Autoinducción de línea bifilar
Calcular el coeficiente de autoinducción por unidad de longitud de una línea bifilar formada por dos hilos conductores rectilíneos, muy largos, de sección circular de radio $a$ y situados paralelos a una distancia $d$.

### 3.- Autoinducción de cable coaxial
Calcular el coeficiente de autoinducción por unidad de longitud de un cable coaxial de radios $a$ y $b$ ($a < b$).

### 4.- Inducción mutua de solenoide y espira pequeña
En el interior de un solenoide recto muy largo, de sección circular de radio $a$ y $n$ vueltas por unidad de longitud, se sitúa centrada una pequeña espira circular de radio $b$ ($a \gg b$) de modo que su eje forma un ángulo $\theta_0$ con el eje del solenoide. Calcular el coeficiente de inducción mutua.

### 5.- Inducción mutua de dos solenoides concéntricos finitos
En el interior de un solenoide muy largo, de $n_1$ espiras por unidad de longitud y radio $a$, se introduce un segundo solenoide de longitud $d$ y radio $b$ ($b < a$) que posee $n_2$ espiras por unidad de longitud. Suponiendo que son coaxiales, obtener el coeficiente de inducción mutua entre ambos arrollamientos.

### 6.- Inducción mutua de dos solenoides infinitos
Determinar el coeficiente de inducción mutua por unidad de longitud en el caso del problema anterior considerando ambos solenoides de gran longitud.

### 7.- Inducción mutua de toroide e hilo axial
Calcular el coeficiente de inducción mutua entre un anillo toroidal de $N$ espiras, de radios $a$ y $b$ y altura $h$, y un hilo conductor muy largo situado en su eje de revolución.

### 8.- Momento dipolar de esfera giratoria
Una esfera, de radio $a$ y densidad superficial de carga uniforme $\sigma$, se hace girar en torno a uno de sus diámetros a una velocidad angular constante $\omega$. Calcular el momento dipolar magnético.

### 9.- Momento dipolar de solenoide
Calcular el momento dipolar magnético asociado a un solenoide de longitud $\ell$ y radio $a$, con $N$ espiras, si circula una corriente $I$.

### 10.- Inducción mutua de dos espiras lejanas
Dos pequeños bucles de corriente circulares, de radios $a$ y $b$, se sitúan en un mismo plano y muy alejados. Calcular el coeficiente de inducción mutua.

### 11.- Energía magnética de solenoide
Calcular la energía magnética por unidad de longitud asociada a un solenoide delgado y de gran longitud $\ell$, radio $a$ y $N$ espiras totales.

### 12.- Autoinducción interna de un hilo
Un hilo conductor rectilíneo muy largo, de sección circular de radio $a$, transporta una corriente $I$. Calcular la energía magnética almacenada por unidad de longitud en su interior. Obtener el coeficiente de autoinducción "interna" del hilo.

### 13.- Energía magnética de un toroide
Sobre un anillo toroidal, de radios interior $a$ y exterior $b$, y altura $h$, se efectúa un bobinado de $N$ espiras que son recorridas por una corriente de intensidad $I$. Hallar la energía magnética almacenada en el anillo.

---

## Hoja 3: Energía y Fuerzas Magnéticas

### 1.- Interacción entre dos anillos coaxiales lejanos
Dos hilos conductores en forma de anillo, de radios $a$ y $b$ ($a \gg b$), están colocados coaxiales en el mismo eje, pero en dos planos diferentes muy alejados entre sí ($z \gg a \gg b$). Por el primero circula una corriente $I$, y el segundo se aleja con una velocidad $v$, que supondremos constante y no excesivamente alta. Obtener:
a) La fuerza electromotriz inducida en el anillo de radio $b$.
b) La corriente que circula por ese anillo, suponiendo $v$ constante y que el anillo tiene una resistencia $R$.
c) La fuerza con la que tenemos que empujar al anillo de radio $b$ para mantener la velocidad constante.

### 2.- Equilibrio de dos dipolos magnéticos giratorios
Dos dipolos $\vec{m}_1$ y $\vec{m}_2$ se sitúan en posiciones fijas a lo largo del eje X, dejándose libertad para que ambos puedan girar respecto al eje Z. ¿Qué posición relativa será la de equilibrio?

### 3.- Bucle rectangular en campo variable espacialmente
Un hilo conductor cerrado de forma rectangular, de lados $a$ y $b$, y resistencia $R$, se desplaza en el plano XY con velocidad $\vec{v} = v_0 \vec{u}_x$ ($v_0$ constante) en una región donde existe un campo:
$$\vec{B} = B_0 \cos(Ax) \vec{u}_z \quad (B_0 \text{ y } A \text{ constantes})$$
Calcular la fuerza mecánica que deberá aplicarse en cada instante para mantener su movimiento uniforme. ¿Qué condiciones hacen la fuerza nula?

### 4.- Fuerza entre hilo infinito y bucle rectangular
Un hilo conductor rectilíneo y muy largo de corriente $I_1$ se encuentra en el mismo plano que un bucle rectangular, de lados $a$ y $b$, por el que circula una corriente $I_2$. Hallar la fuerza magnética entre ambos circuitos.

### 5.- Muelle magnético
Un muelle, de sección circular de radio $a$ y $N$ vueltas, y longitud $L$, se suspende verticalmente. En sus extremos se disponen sendos contactos deslizantes que, conectados a una fuente, hacen que circule una corriente $I$. En el extremo inferior se cuelga un peso $\vec{P}$. Calcular la corriente necesaria para que el muelle no se deforme.

### 6.- Placa móvil en campo magnético
Una placa metálica muy larga, de sección transversal rectangular de dimensiones $a$ y $b$, se desplaza con velocidad $\vec{v} = v_0 \vec{u}_x$ constante (ver figura). Se disponen dos contactos deslizantes que hacen circular una corriente $I$, y se introduce en un campo uniforme $\vec{B} = B_0 \vec{u}_y$ perpendicular. ¿Qué fuerza habrá que aplicar para que se mantenga a la misma velocidad $\vec{v}$ inicial?

### 7.- Par entre dos bucles concéntricos
Dos bucles circulares de radios $a$ y $b$ ($b \ll a$) se sitúan en un mismo plano concéntricos y se fijan de modo que únicamente el bucle menor puede girar libremente respecto a uno de sus diámetros. Si se hacen circular corrientes $I_1$ e $I_2$, respectivamente, y en un instante determinado el ángulo que forman las normales a ambos bucles es $\theta$, ¿cuál es el par que aparece sobre el circuito móvil?

### 8.- Bucle circular aplanado por un lado
Un bucle de corriente plano de forma circular, de radio $a$, se "aplana" por uno de sus lados, de forma que su perímetro queda como se representa en la figura (con ángulo central de apertura $2\alpha$). El bucle transporta una corriente de intensidad $I_1$. Perpendicular al plano del mismo, y pasando por su centro, se encuentra un hilo conductor muy largo de intensidad de corriente $I_2$. Calcular la fuerza y el par que aparecen sobre nuestro bucle.


---

# Tema 8: Circuitos en Régimen Transitorio y Señal Alterna

## Hoja 1: Circuitos Eléctricos: Régimen Transitorio y Señal Alterna

### 1.- Descarga de condensador sobre otro idéntico
Se dispone de dos condensadores idénticos, de capacidad $C$. Uno de ellos está cargado con una carga $Q_0$, mientras el otro está inicialmente descargado. En un instante de tiempo se conectan mediante un hilo metálico de conductividad $\gamma$, longitud total $l$ y sección $S$. Calcular:
a) La evolución de la corriente que circula por el sistema.
b) La energía inicial y final almacenadas en los condensadores. Demostrar que la diferencia entre la energía inicial y la final coincide con la energía disipada por efecto Joule en el hilo metálico.

### 2.- Transitorio en circuito de varias ramas
Dado el circuito de la figura, estudiar cómo evoluciona la corriente en cada rama al cerrar el interruptor (régimen transitorio).
*(Nota: El circuito típicamente consta de una fuente de f.e.m. con resistencias y bobinas/condensadores en paralelo o en ramas distintas).*

### 3.- Circuito puente con interruptor
Una batería $E$ con resistencia interna $r$, dos resistencias $R_1 = 10r$ y $R_2 = 5r$, y dos condensadores $C_1$ y $C_2$ tales que $C_1 = 2C_2$ se conectan como en la figura. Los condensadores están descargados inicialmente.
a) Se cierra el interruptor en $t=0$, ¿cuál es la diferencia de potencial entre A y C (es decir, $V_{AC} = V_A - V_C$) en el instante posterior? ¿Y la diferencia de potencial entre B y C?
b) Después de un tiempo lo bastante largo, cuando se llegue a un estado estacionario, ¿cuáles serían los valores de $V_{AC}$ y $V_{BC}$?
c) Escribir un sistema de ecuaciones que nos permita resolver la evolución temporal de las tres corrientes indicadas en la figura (no es necesario resolverlo).
*Ahora se cortocircuitan los puntos A y B mediante un hilo de resistencia despreciable:*
d) ¿Circulará alguna corriente por ese hilo? ¿En qué sentido?
e) ¿Cuáles serían ahora los valores finales de $V_{AC}$ y $V_{BC}$?
f) ¿Qué carga total habrá circulado a través de ese hilo? ¿Es consistente con la respuesta d?
*(Expresar todas las respuestas en función de $E$, $r$ y $C_2$).*

### 4.- Circuito RLC serie en alterna
Un circuito serie consta de una autoinducción de $25\,\text{mH}$, un condensador de $50\,\mu\text{F}$ y una resistencia $R$ conectados a un generador de $120\,\text{V}$ y frecuencia angular $400\,\text{rad/s}$. Sabiendo que la corriente adelanta a la tensión en $63.4^\circ$, determinar el valor de la resistencia y la caída de tensión en cada elemento.

### 5.- Circuito con fuentes senoidales acopladas
Resolver el circuito suponiendo que las fuentes de la figura varían con el tiempo según las expresiones:
$$v_s(t) = 7\cos(\omega t)\,\text{V} \quad \text{y} \quad i_s(t) = 8.5\cos(\omega t)\,\text{A}$$

### 6.- Instalación eléctrica industrial (Cálculo de potencias)
La carga de una instalación de $660\,\text{V}_{\text{rms}}$ en sus terminales consume $52.8\,\text{kW}$ con un factor de potencia del $80\%$ en adelanto (capacitivo). Sabiendo que la frecuencia de trabajo es de $50\,\text{Hz}$:
a) Calcular la potencia compleja y la potencia reactiva requeridas por la carga.
b) Tomando como referencia el voltaje aplicado, obtener el fasor de corriente.
c) ¿Qué valor tiene la impedancia equivalente de la carga?

### 7.- Teorema de Máxima Transferencia de Potencia
Si tenemos una fuente no ideal de tensión $\tilde{V}$ con una impedancia de salida $Z_g = R_g + j X_g$, calcular la impedancia de carga $Z = R + j X$ que hace máxima la transferencia de potencia activa a la misma (ley de Jacobi o adaptación de impedancias).

### 8.- Potencias en un condensador
Calcular el voltaje en el condensador, $V_c(t)$, así como las potencias activa, reactiva, aparente y compleja asociadas a este elemento, dadas las fuentes del circuito:
$$i_g(t) = 7\cos(10^3 t)\,\text{A} \quad \text{y} \quad v_g(t) = 10\cos(10^3 t)\,\text{V}$$

### 9.- Circuito de corriente alterna domiciliaria
El generador del circuito de la figura proporciona un voltaje:
$$v_g(t) = 240\cos(2\pi 50 t)\,\text{V}$$
Determinar la corriente en cada rama, así como las potencias medias, reactivas, aparentes y complejas en cada rama.

### 10.- Potencia disipada en circuito de alterna
Calcular la potencia total disipada en el circuito, dado que $V_1 = 10\,\text{V}$ y la frecuencia es $f = 50\,\text{Hz}$.


---

# Tema 9: Campo Magnético en Medios Materiales

## Hoja 1: Materiales con Magnetización Prefijada (Imanes)

### 1.- Imán cilíndrico longitudinal
Un imán cilíndrico, de radio $a$ y longitud $L$, está caracterizado por una imanación longitudinal uniforme $\vec{M}_0$. Calcular el campo magnético $\vec{H}$ y la inducción magnética $\vec{B}$ en puntos de su eje.
*Datos:* $L = 0.2\,\text{m}$, $a = 30\,\text{cm}$, $M_0 = 15 \cdot 10^3\,\text{A/m}$.

### 2.- Dos imanes enfrentados
Dos imanes en forma de barra, con magnetizaciones longitudinales uniformes $\vec{M}_1$ y $\vec{M}_2$, se disponen alineados dejando una pequeña separación y se fija su posición. Suponiendo ambas barras de gran longitud y que están en aire, calcula el campo de inducción magnética $\vec{B}$ y la intensidad de campo magnético $\vec{H}$ en tres puntos del eje del sistema, muy próximos a los extremos enfrentados de los imanes:
a) Punto 1: dentro de la barra de magnetización $\vec{M}_1$
b) Punto 2: dentro de la barra de magnetización $\vec{M}_2$
c) Punto 3: en el espacio intermedio (sin imanación)
d) ¿Qué sucede si $\vec{M}_1 = -\vec{M}_2$? ¿Y si $\vec{M}_1 = \vec{M}_2$?

### 3.- Cilindro con magnetización azimutal
Un cilindro recto de sección de radio $a$ y muy largo está magnetizado según:
$$\vec{M} = M_0 \frac{r}{a}\vec{u}_\phi$$
donde $M_0$ es una constante (A/m) y $r$ es la distancia de un punto al eje. Calcular las corrientes de magnetización, el campo de inducción magnética $\vec{B}$ y el campo magnético $\vec{H}$ en cualquier punto.

### 4.- Cable coaxial con medio magnetizado azimutalmente
Se dispone de dos conductores cilíndricos, coaxiales, de espesores despreciables, longitud $L$ y radios $a$ y $b$, respectivamente, siendo $L \gg b > a$. En el espacio intermedio se coloca una pieza material cilíndrica, coaxial con los conductores, de longitud $L$, radio interior $c$ y exterior $b$ ($a < c < b$) de un material no lineal con una magnetización dada por:
$$\vec{M} = \frac{M_0}{\rho}\vec{u}_\phi$$
siendo $M_0$ una constante y $\rho$ la distancia al eje. Si circula una corriente $I$ por el conductor interior, que regresa por el exterior, ambas distribuidas uniformemente, determinar:
a) Los vectores inducción magnética e intensidad magnética en cualquier punto del espacio. Representar la distribución de líneas de campo en ambos casos.
b) Las densidades de carga magnética y corriente (reales y ficticias) que aparecen en el sistema.

### 5.- Imán toroidal con entrehierro
Un imán toroidal de sección rectangular, con radios interior $a$ y exterior $b$ y altura $h$, posee una magnetización:
$$\vec{M} = \frac{A_0}{r}\vec{u}_\phi$$
siendo $r$ la distancia al eje del toroide y $A_0$ una constante (A). Se ha efectuado un entrehierro de ángulo $\theta_0 \ll 2\pi$. Suponiendo que la magnetización en el resto del material no se ha modificado apreciablemente, ¿qué valor tienen los campos $\vec{B}$ y $\vec{H}$ en el núcleo? ¿Y en el entrehierro?

### 6.- Esfera uniformemente magnetizada
Una esfera de radio $a$ de un cierto material ferromagnético está imanada permanentemente con una magnetización uniforme $\vec{M}$. Calcular el campo magnético $\vec{H}$ y la inducción magnética $\vec{B}$ en el centro de la esfera.

### 7.- Cavidad esférica en medio magnetizado
En un medio magnético ilimitado que posee una magnetización permanente uniforme $\vec{M}$, se ha originado una cavidad esférica de radio $a$. Calcular el campo magnético $\vec{H}$ en el centro de la misma (nota: antes de originar la cavidad, el campo en ese punto era $\vec{B}_0 = \mu_0 (\vec{H}_0 + \vec{M})$).

---

## Hoja 2: Materiales Lineales

### 1.- Solenoide infinito con núcleo lineal
Un solenoide recto y muy largo tiene $n$ espiras por unidad de longitud. Calcular los campos magnéticos $\vec{B}$ y $\vec{H}$ en su interior cuando circula una corriente de intensidad $I$. Repetir el cálculo si el solenoide se llena con un material magnéticamente lineal e isótropo de susceptibilidad $\chi_m$.
*Datos:* $n = 20\,\text{espiras/mm}$, $I = 3\,\text{A}$, $\chi_m = 20$.

### 2.- Hilo conductor recubierto de material magnético
Un hilo rectilíneo infinito de sección circular de radio $a$ y que transporta una corriente $I$, se recubre con una capa de radio $b$ ($b > a$) de material magnético de permeabilidad $\mu$. Calcular la inducción magnética $\vec{B}$ en cualquier punto, y el vector magnetización $\vec{M}$ y las corrientes de magnetización en el material.

### 3.- Coaxial con dos capas dieléctrico-magnéticas
El espacio interior de un cable coaxial, de radios $a$ y $b$ y gran longitud $L$, que transporta una corriente $I$, está ocupado por dos capas coaxiales de permeabilidades $\mu_1$ y $\mu_2$, siendo $c$ el radio de la superficie de separación ($a < c < b$). Calcular los campos $\vec{H}$ y $\vec{B}$ y el vector magnetización $\vec{M}$. Repetir con dos materiales no coaxiales (uno ocupa la mitad inferior y el otro la superior del cable).

### 4.- Autoinducción de solenoide con núcleo parcial
Calcular la autoinducción por unidad de longitud de un solenoide muy largo de radio $a$ y $n$ espiras por unidad de longitud, en cuyo interior y de forma coaxial, se encuentra situada una barra cilíndrica de radio $b$ ($a > b$) de material magnético de permeabilidad $\mu$.

### 5.- Toroide con dos capas de permeabilidad
Un núcleo magnético toroidal, de sección rectangular, radios $a$ y $c$ y altura $h$, posee dos capas coaxiales de permeabilidades $\mu_1$ y $\mu_2$, siendo $b$ el radio de la superficie de separación ($a < b < c$). Calcular el flujo magnético al bobinar $N$ espiras y circular una intensidad $I$.

### 6.- Toroide con entrehierro y núcleo lineal
Un anillo toroidal, de radios $a$ y $b$ y altura $h$, se talla con material de permeabilidad $\mu$. Se efectúa un entrehierro retirando la cuña de material delimitada por dos planos que se cortan en el eje y forman un ángulo $\theta_0$. El anillo se rodea con $N$ espiras por las que circula una corriente $I$. Calcular el campo magnético $\vec{H}$ suponiendo que no hay pérdidas de flujo magnético ($\theta_0 \ll 2\pi$).

### 7.- Fuerza sobre núcleo deslizante en solenoide
En el interior de un solenoide de longitud $d$, sección transversal $A$ y $N$ espiras de corriente $I$, se introduce parcialmente una barra de igual sección y área $A$, y de material magnético de permeabilidad $\mu$. Despreciando efectos de borde, hallar la fuerza sobre el material.

### 8.- Parámetros e histéresis de un transformador
En un transformador rectangular, de base $a$ y altura $b$, y sección $S$ (para simplificar, supongamos que $a^2, b^2 \gg S$). Se arrolla un primario con $N_1$ vueltas y un secundario con $N_2$ vueltas. El transformador está compuesto por un material ferromagnético blando de permeabilidad $\mu \gg \mu_0$.
a) Calcular la autoinducción del bobinado primario ($L_1$), la del secundario ($L_2$) y la inductancia mutua entre ambos ($M_{12}$).
b) Si conectamos el primario a una fuente de fuerza electromotriz $\xi = \xi_0 \cos(\omega t)$ y el secundario se mantiene en circuito abierto, ¿cuál sería la diferencia de potencial entre los terminales del secundario?
c) Supongamos que el material ferromagnético tiene un valor de saturación $B_s$ y que $\xi_0$ es lo suficientemente alto como para llegar a ese valor durante una parte del ciclo. Representar la evolución temporal de la diferencia de potencial en esa situación.

---

## Hoja 3: Materiales No Lineales (Histéresis)

### 1.- F.e.m. inducida en toroide con histéresis ideal
Un toroide, de radios $a$ y $b$ y altura $h$, se talla con un material cuya curva de imanación se puede describir como:
$$B = \begin{cases} B_s \frac{H}{H_c} & \text{si } |H| < H_c \\ \pm B_s & \text{si } |H| \ge H_c \end{cases}$$
donde $B_s$ y $H_c$ corresponden a los valores de la inducción magnética de saturación y el campo magnético coercitivo. Situado en su eje, un hilo conductor muy largo transporta una corriente que varía linealmente con el tiempo:
$$I(t) = kt \quad (k = \text{cte.})$$
Si se realiza sobre el toroide un bobinado de $N$ vueltas, ¿cuál es la f.e.m. inducida en dicho bobinado en función del tiempo?
*Datos:* $a = 5\,\text{cm}$, $b = 10\,\text{cm}$, $h = 1\,\text{cm}$, $H_c = 1\,\text{kA/m}$, $k = 6.28\,\text{A/s}$, $N = 1000$, $B_s = 1\,\text{T}$.

### 2.- Curva inducida por ciclo de histéresis real
Utilizando un material ferromagnético que presenta un ciclo de histéresis real, se talla un núcleo toroidal delgado de radio medio $a$. El toroide se bobina con $N$ espiras por las que circula una corriente senoidal de amplitud $I_0$. Representar gráficamente, de forma cualitativa, la f.e.m. inducida en un segundo bobinado efectuado sobre el mismo núcleo.
*Datos:* $a = 10\,\text{cm}$, $N = 10^3$, $I_0 = 200\,\text{mA}$.

### 3.- Electroimán con ley de primera imanación cuadrática
Sobre el núcleo de un electroimán de sección constante $S$, longitud media $L$ y entrehierro de anchura $L_0$, se realizan dos arrollamientos de $N_1$ y $N_2$ espiras. El material del núcleo es ferromagnético de ciclo de histéresis mostrado en la figura, pudiendo ajustarse la curva de primera imanación a la función:
$$B = 6.9 \cdot 10^{-9} H^2 \quad \text{si } H < 17000\,\text{A/m}$$
$$B_s = 2\,\text{T} \quad \text{si } H \ge 17000\,\text{A/m}$$
El material no ha sufrido primera imanación.
a) Si por el primer bobinado se hace circular una corriente $I_1$, ¿qué corriente $I_2$ deberá circular por el otro arrollamiento para llevar el material a saturación?
b) Calcular el valor del campo magnético $\vec{H}$ si las corrientes se hacen nulas tras saturación (campo coercitivo o remanente).
*Datos:* $L = 1\,\text{m}$, $L_0 = 1\,\text{cm}$, $N_1 = 10^4$, $N_2 = 5000$, $I_1 = 2\,\text{A}$.


---

# Tema 10: Ecuaciones de Maxwell y Ondas Electromagnéticas

## Hoja 1: Ecuaciones de Maxwell (Parte I)

### 1.- Campo magnético inducido por campo eléctrico lineal
En una región del espacio totalmente vacía hay un campo eléctrico dado por la expresión $\vec{E} = kt \vec{u}_z$ ($k$ es una constante conocida y $t$ es el tiempo), además de un campo magnético $\vec{B}$ en dirección del eje x. Encontrar una expresión para ese campo $\vec{B}$.

### 2.- Condensador cargado por corriente constante (Corriente de Desplazamiento)
Un condensador de placas planoparalelas, circulares, de radio $a$, muy próximas, se carga conectándolo a un hilo rectilíneo, muy delgado y largo, por el que circula una corriente de pequeña intensidad constante $I$.
a) Expresar el campo eléctrico $\vec{E}$ y el vector desplazamiento $\vec{D}$ en función de la carga $q$ del condensador.
b) Calcular la corriente de desplazamiento.
c) Obtener el campo magnético $\vec{H}$ durante el proceso de carga y verificar las condiciones de contorno.
d) ¿Qué distribución de corriente de conducción existe sobre las placas?

### 3.- Balance energético en condensador (Vector de Poynting)
En el problema anterior:
a) Encontrar el vector de Poynting sobre la superficie límite de la región interna, entre las armaduras del condensador.
b) Calcular la energía por unidad de tiempo que entra en dicha región.
c) Comprobar que la potencia calculada coincide con el aumento en el tiempo de la energía electrostática almacenada en el condensador.

### 4.- Condensador con placas oscilantes conectado a batería
Un condensador de placas planoparalelas, circulares, de radio $a$, muy próximas, se conecta a una batería de f.e.m. constante $V_0$. A continuación, se hacen oscilar las placas muy lentamente, de modo que permanecen paralelas, variando la distancia de separación según:
$$d(t) = d_0 + d_1 \sin(\omega t)$$
Encontrar el campo magnético $\vec{H}$ que se origina entre placas.

### 5.- Condensador con placas oscilantes aislado
Obtener el campo magnético $\vec{H}$ entre las placas del condensador del problema anterior, suponiendo que se desconecta de la batería, una vez cargado, y posteriormente se hacen oscilar las placas en la forma indicada.

### 6.- Poynting en hilo conductor macizo
Un conductor cilíndrico, de radio $a$, muy largo y de material de conductividad $\gamma$, transporta una corriente estacionaria en dirección longitudinal uniformemente distribuida con densidad $\vec{J}$. Calcular el vector de Poynting en la superficie exterior del conductor. ¿Cambiará la dirección del flujo de energía del conductor anterior si se intercambian las conexiones de la batería que mantiene la d.d.p. entre sus extremos?

### 7.- Poynting de hilo cargado paralelo a plano a tierra
Un hilo conductor rectilíneo muy largo está colocado sobre una placa conectada a tierra, está cargado con una densidad lineal $\lambda$ y transporta una corriente $I$. Obtener el valor del vector de Poynting en un punto situado entre el hilo y el plano.

---

## Hoja 2: Ecuaciones de Maxwell (Parte II)

### 8.- Descarga de condensador cilíndrico con dieléctrico conductor
Un condensador cilíndrico, muy largo, de radios interior $a$ y exterior $b$, posee una densidad de carga $\lambda$ por unidad de longitud. La región entre los conductores se encuentra totalmente ocupada por un material dieléctrico, no magnético, de permitividad próxima a la del vacío y de conductividad $\gamma$, de forma que existe un flujo de carga entre los conductores que está descargando el condensador ($\lambda = \lambda(t)$).
a) Comprobar que $\vec{H}$ es nulo en el interior.
b) ¿Qué energía se disipa por unidad de tiempo y por unidad de volumen a una distancia $r$ del eje de simetría?
c) Calcular la potencia total disipada para una longitud $L$ del condensador.
d) Demostrar que dicha potencia coincide con la disminución temporal de la energía del condensador.

### 9.- Poynting en cable coaxial de transmisión
Un cable coaxial, muy largo, de radios interior $a$ y exterior $b$, se utiliza como línea de transmisión entre una batería $V_0$ y una carga resistiva de valor $R$.
a) Calcular el vector de Poynting en la zona interna del cable.
b) Demostrar que la potencia total transportada por el cable es igual a $V_0^2 / R$.
c) Estudiar la dirección del flujo de energía al intercambiar los terminales de la batería.

### 10.- Modelo físico de rayo de Thor (Transitorio y campos)
De todos es conocida la capacidad del dios nórdico Thor para invocar el rayo, utilizando su martillo Mjölnir. Para ello, al alzar su martillo, atrae una carga que forma una nube de radio $a$ y a una altura $h$. En el suelo se acumula una carga igual de signo opuesto, hasta que el campo eléctrico supera el de ruptura en el aire $E_0$. En ese momento se descarga la energía acumulada, saltando el rayo. Si llamamos $R$ a la resistencia del canal conductor por el cual se descarga el rayo (en el centro del sistema, y que aproximaremos como una línea recta vertical), calcular:
a) La carga inicial del sistema (en función de $E_0$) cuando se produce la ruptura.
b) La evolución de carga y corriente eléctrica tras iniciarse la descarga (suponer que la descarga es lo bastante lenta como para poder despreciar efectos inductivos).
c) El valor del campo magnético en el espacio entre la nube y el suelo, así como en el exterior.
d) El valor del vector de Poynting también en el espacio entre la nube y el suelo.
e) Comentar el resultado, así como las aproximaciones realizadas. ¿De dónde sale la energía que se consume por efecto Joule en el rayo? ¿Cómo llega hasta el canal conductor?

---

## Hoja 3: Ecuaciones de Maxwell (Parte III)

### 11.- Placas paralelas alimentadas conectadas por bloque conductor
Tenemos un sistema formado por dos placas metálicas perfectamente conductoras, planas y paralelas. En una zona alejada de los dos extremos se conectan mediante un bloque conductor de permeabilidad $\mu$ y conductividad $\gamma$ (ver figura). El sistema se alimenta mediante una fuente de corriente continua que proporciona una corriente $I$.
a) Despreciando efectos de borde, asumimos que el campo magnético es de la forma $\vec{H} = H(x)\vec{u}_z$. Si la corriente se distribuye uniformemente en el bloque conductor, obtener la expresión de $H(x)$.
b) Obtener la energía total almacenada en el sistema.
c) Obtener la fuerza total sobre el bloque conductor. ¿Depende de $\mu$? Justificar la respuesta.
d) La potencia transportada desde la fuente de corriente hacia el bloque conductor.
e) La potencia disipada en el bloque conductor, ¿coincide con el valor anterior?
f) La resistencia, inductancia y capacidad equivalentes del sistema. Realizar un esquema del circuito equivalente.

---

## Hoja 4: Propagación de Ondas Planas

### 1.- Onda plana en dieléctrico ideal
Una onda plana electromagnética de frecuencia $600\,\text{MHz}$ se propaga en dirección $+z$ en un dieléctrico sin pérdidas de permitividad relativa $\varepsilon_r = 4$ y permeabilidad próxima a la del vacío. Sabiendo que el valor máximo del campo eléctrico es $5\,\text{V/m}$, se pide:
a) Calcular la constante de fase, la impedancia de onda, la velocidad de fase y la longitud de onda.
b) Obtener el promedio temporal de la densidad de energía.
c) ¿Cuál es el valor de la densidad de energía media?

### 2.- Incidencia normal sobre conductor de plata
Una onda plana viaja en dirección $+Z$ en el vacío ($z < 0$) e incide de forma normal en $z = 0$ sobre un cuerpo de plata ($z > 0$) de conductividad $\gamma = 61.7\,\text{MS/m}$. Sabiendo que la frecuencia de la onda es $f = 1.5\,\text{MHz}$ y que el campo eléctrico en $z = 0$ se expresa como $\vec{E}(0, t) = 10 \cos(\omega t) \vec{u}_x\,\text{V/m}$, obtener para $z > 0$:
a) El campo magnético y la profundidad de penetración.
b) La longitud de onda y la velocidad de fase.

### 3.- Calentamiento de microondas (chuleta de cordero)
Se quieren descongelar unas chuletas de cordero mediante un horno de microondas que opera a $2.45\,\text{GHz}$. A esa frecuencia la permitividad relativa de la carne de cordero es 15 y su conductividad $10\,\Omega^{-1}\text{m}^{-1}$. Calcular la profundidad de penetración de la onda en la carne y comentar la efectividad del método.

### 4.- Superposición de dos ondas simétricas
Dos ondas planas de la misma frecuencia $f_0 = 10\,\text{MHz}$ se propagan en el vacío en el plano XY siguiendo sendas direcciones simétricas con respecto al eje X con ángulos respectivos $\theta$ y $-\theta$. Los campos eléctricos son de la misma amplitud $E_0$, paralelos al eje Z y vibran en fase en el origen de coordenadas.
a) Calcular el campo eléctrico y el campo magnético de la onda resultante.
b) Obtener la velocidad de fase y la longitud de onda.
c) Calcular el valor medio temporal de la potencia transportada por la onda resultante a través de una superficie rectangular $A$ paralela al plano YZ.

### 5.- Superposición de ondas y promedio del vector de Poynting
Cada una de las siguientes ondas planas cuyo campo eléctrico viene dado por:
1) $\vec{E} = E_{01} e^{j(kz - \omega t + \phi_1)} \vec{u}_x + E_{02} e^{j(kz - \omega t + \phi_2)} \vec{u}_y$
2) $\vec{E} = E_{01} e^{j(kz - \omega t + \phi_1)} \vec{u}_x + E_{02} e^{j(kz - \omega t + \phi_2)} \vec{u}_x$
puede considerarse, a su vez, como la superposición de dos ondas independientes, siendo en 1) los campos eléctricos perpendiculares y en 2) paralelos. Encontrar $\langle\vec{S}\rangle$ y demostrar que sólo en el primer caso es igual a la suma de los vectores de Poynting promedio de cada una de las componentes.


---

