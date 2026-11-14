---
title: "Historias de datos del maíz: tres borradores"
lang: es
---

**Equipo:** IngCarac2026Unison · Maestría en Ciencia de Datos, Universidad de Sonora
**Estado:** borrador para discusión, 9 de noviembre de 2026

Este documento tiene tres versiones posibles de la historia de datos del proyecto, escritas a partir
de lo que ya encontramos en las libretas (SNIIM, DGSIAP y Yahoo Finance). Cada una usa los mismos
datos pero sigue un hilo distinto. La idea es leerlas, escoger una (o combinar partes) y después
armar las gráficas que la acompañen.

Todas las cifras están en pesos corrientes (sin deflactar). El precio "al productor" es el precio
medio rural del DGSIAP para maíz grano, ponderado por volumen. El precio "mayorista" es la mediana
del maíz blanco en cinco centrales de abasto del SNIIM: Culiacán, Guadalajara, Guadalupe (Monterrey),
Hermosillo e Iztapalapa (CDMX). Los textos marcados con **[pendiente]** necesitan un dato que todavía
no tenemos.

<div style="page-break-before: always"></div>

# Historia 1 · ¿Quién paga el maíz caro?

*Hilo: seguir el precio del maíz por la cadena, del campo a la tortilla, y ver en qué eslabón se
queda el golpe.*

### El choque

Entre 2020 y 2023 el maíz en México tuvo el choque más grande de la última década. En las centrales
de abasto, el kilo de maíz blanco pasó de alrededor de 6 pesos en 2020 a 10 pesos en 2022. Primero
llegó la pandemia, que desordenó cadenas de suministro y fletes. Después, en febrero de 2022, Rusia
invadió Ucrania, uno de los grandes exportadores de granos del mundo. En los tres meses siguientes
a la invasión, el maíz mayorista subió 16 %, una de las subidas más fuertes de todo el periodo.

Un aumento así lo tiene que pagar alguien. Para saber quién, seguimos el precio por la cadena:
el agricultor que lo siembra, el mercado mayorista que lo mueve, la empresa que lo convierte en
harina y el consumidor que compra la tortilla.

### La empresa: casi no se movió

Empezamos por Gruma, la mayor productora de harina de maíz del mundo. Si el maíz es su principal
insumo, esperaríamos que un maíz caro le pegara a la acción. No fue así. Mes a mes, la correlación
entre el cambio del precio del maíz y el rendimiento de Gruma está entre −0.10 y 0.14 en los cinco
mercados, y ninguna es significativa, ni en el mismo mes ni con hasta tres meses de rezago.

Es más: los años del maíz caro fueron buenos años para la acción. Gruma ganó 24 % en 2020, 13 % en
2021, 3 % en 2022 y 22 % en 2023. Solo hubo un momento en que el maíz y Gruma se movieron fuerte al
mismo tiempo: la invasión a Ucrania, cuando la acción cayó 15 % en tres meses. Fue un episodio y se
recuperó.

¿Por qué una empresa resiste que su materia prima se duplique? Hay varias razones posibles. Más de
la mitad de sus ventas son en Estados Unidos y en dólares. Compra grandes volúmenes y se puede
cubrir con contratos a futuro. Y tiene margen para subir sus propios precios. Con nuestros datos no
podemos decir cuál pesa más, pero sí podemos decir que el golpe no se quedó en su acción.

### El agricultor: gana poco cuando sube y pierde todo cuando baja

Pasemos al otro extremo. El DGSIAP registra cuánto le pagaron al productor por su maíz en el campo.
En 2018 recibía 3.86 pesos por kilo, mientras el mismo maíz se vendía en 5.91 en la central de
abasto. Al productor le tocaba el 65 % del precio mayorista.

Cuando llegó el choque, el precio subió para todos. En 2022 el productor recibió 6.48 pesos y el
mayorista llegó a 10. Su parte seguía en 65 %. Hasta aquí la cadena fue pareja.

El problema vino de bajada. De 2022 a 2025 el precio al productor cayó 20 %, de 6.48 a 5.18 pesos.
En la central de abasto la mediana nacional no bajó de 10 pesos, y en mercados como Hermosillo siguió
subiendo hasta 13. La parte del productor bajó a 57 % en 2024 y a 52 % en 2025. La diferencia entre
lo que recibe el campo y lo que cuesta en el mercado pasó de 2 pesos por kilo en 2018 a casi 5 en
2025: se multiplicó por 2.4.

*(Esa diferencia incluye flete, acopio, almacenamiento e intermediación, así que no es pura ganancia
de nadie. Lo que sí muestra es que, cuando el precio bajó, la baja llegó al campo y no al mercado.)*

### Sinaloa: perder la cosecha y también el precio

En un mercado normal, si se pierde una cosecha el precio debería subir y compensar en parte a los
productores. En 2024 y 2025 una sequía histórica en Sinaloa, el estado que más maíz produce, hundió
su producción de 6.7 a 2.3 millones de toneladas. La producción nacional cayó de unos 27 a 24
millones de toneladas.

El precio no subió: siguió bajando. El faltante se cubrió con maíz importado, en un momento en que
el maíz internacional estaba barato. El productor sinaloense perdió dos veces: tuvo menos maíz que
vender y lo vendió más barato que en 2022 (5,808 pesos por tonelada en 2025 contra 6,749 en 2022).

### El consumidor: lo que subió no bajó

En el otro extremo de la cadena está la tortilla. **[pendiente: precio de la tortilla por kilo,
2018–2025, del SNIIM o del INPC del INEGI.]** Si se confirma lo que esperamos, la tortilla subió
durante el choque y no regresó cuando el maíz bajó en el campo. El consumidor pagó el aumento y no
recibió la baja.

### Cierre

En noviembre de 2025, productores del Bajío bloquearon carreteras para exigir un precio de garantía
para el maíz blanco, y el gobierno terminó negociando con ellos. Nuestros datos ayudan a entender
por qué. En la cadena del maíz, los dos extremos absorbieron el choque: el agricultor, que vende
cada vez una parte más pequeña del precio final, y el consumidor, que paga la tortilla. El centro
de la cadena, la intermediación y la gran industria, pasó el episodio prácticamente sin daño.

*Alcance: es un análisis descriptivo. Las asociaciones que mostramos no prueban causalidad.*

<div style="page-break-before: always"></div>

# Historia 2 · La historia que no encontramos

*Hilo: contar el proyecto como una investigación. Teníamos una hipótesis, los datos la
desmintieron, y lo que encontramos en su lugar es más interesante.*

### La hipótesis

La tortilla es la base de la dieta mexicana y Gruma es la empresa que más harina de maíz produce en
el mundo. Nuestra hipótesis era sencilla: si el maíz es su principal insumo, cuando el maíz se
encarece la empresa gana menos y su acción debería bajar. Si eso fuera cierto, el precio del maíz
en las centrales de abasto nos daría una señal anticipada del rendimiento de Gruma en la Bolsa.

Para probarlo juntamos trece años de datos (2013–2025): precios mensuales del maíz blanco en cinco
mercados del SNIIM, la producción de cada municipio del país del DGSIAP y el precio diario de la
acción de Gruma de Yahoo Finance.

### Lo que no encontramos

La relación no existe. En los cinco mercados, la correlación entre el cambio del precio del maíz y
el rendimiento mensual de Gruma está entre −0.10 y 0.14. Ninguna es significativa. Buscamos de
todas las formas razonables: quitando valores extremos, separando por periodos (antes, durante y
después de la pandemia), usando un solo origen del grano por mercado y dando a la acción de uno a
tres meses para reaccionar. El resultado siempre fue el mismo.

Ni siquiera el choque más grande de la década cambió la conclusión. Entre 2020 y 2023 el maíz
mayorista pasó de unos 6 a 10 pesos el kilo, y esos fueron años buenos para Gruma: +24 % en 2020 y
+22 % en 2023. En cifras anuales la relación incluso sale al revés de lo esperado: los años de maíz
caro fueron años buenos para la acción.

### Lo que sí mueve a Gruma

Si el maíz no explica a Gruma, ¿qué la explica? Revisamos doce eventos de 2017 a 2025 y medimos cómo
se movió la acción en los tres meses siguientes a cada uno. Los movimientos fuertes no vienen del
campo mexicano, sino del comercio con Estados Unidos y del tipo de cambio:

- Al iniciar la renegociación del TLCAN, en agosto de 2017, la acción cayó 11.5 %.
- Con la llegada de la pandemia, en marzo de 2020, subió 37 %. Una explicación posible: con el peso
  depreciado, las ventas en dólares valen más pesos.
- Con los aranceles generales de Estados Unidos, en abril de 2025, cayó 12.6 %.

Tiene sentido: cerca del 55 % de las ventas de Gruma son en Estados Unidos. Para el inversionista,
Gruma es tanto una empresa de comercio exterior como una de maíz.

El único evento que movió a la vez al maíz y a Gruma fue la invasión rusa a Ucrania: el maíz subió
16 % y la acción cayó 15 %, justo como decía nuestra hipótesis. Pero fue un caso entre doce. Los
decretos contra el maíz transgénico, la creación de Segalmex y el panel del T-MEC no dejaron huella
clara en ninguna de las dos series.

### Una sorpresa más: la sequía que no subió el precio

La segunda hipótesis que cayó fue la de la oferta. En 2024 y 2025 Sinaloa vivió la peor sequía de su
historia y su producción de maíz cayó de 6.7 a 2.3 millones de toneladas. Esperábamos que el precio
subiera. Siguió bajando: el faltante se cubrió con importaciones, en un momento de maíz
internacional barato. El precio del maíz en México responde más al mercado mundial que a la
cosecha nacional.

### Lo que aprendimos

Un resultado nulo también es un hallazgo. El precio regional del maíz no es una buena señal para
invertir en Gruma, y entender por qué nos llevó a ver que la empresa está más expuesta al dólar y al
comercio con Estados Unidos que al campo mexicano. Para la siguiente etapa vamos a incorporar el
tipo de cambio, el precio internacional del maíz (futuros de Chicago), indicadores del INEGI y el
ciclo agrícola (otoño-invierno y primavera-verano), como nos sugirió el Dr. Adán Dionicio Flores
Corral (CIPES).

Y queda una pregunta abierta: si la empresa no absorbe los cambios del precio del maíz, ¿quién lo
hace? *(Esta pregunta es el puente a la Historia 1.)*

<div style="page-break-before: always"></div>

# Historia 3 · Un choque, cinco Méxicos

*Hilo: el mismo choque mundial visto desde cinco ciudades. "El precio del maíz" en México es en
realidad muchos precios.*

### Un solo país, muchos precios

Cuando las noticias hablan del "precio del maíz" parece que existe un solo número. En los datos del
SNIIM encontramos otra cosa. Medimos qué tanto se mueven juntos los precios de cinco centrales de
abasto: Culiacán, Guadalajara, Guadalupe (Monterrey), Hermosillo e Iztapalapa (Ciudad de México).
La correlación más alta entre dos de ellos es apenas 0.30, entre Guadalajara y Guadalupe. Los demás
pares se mueven casi de forma independiente. Cada mercado tiene su historia, su origen del grano y
su ritmo.

En 2013 el kilo de maíz blanco ya costaba distinto en cada ciudad: 4.50 pesos en Culiacán, al lado
de los campos de Sinaloa, y 6 pesos en Monterrey, lejos de ellos. Esa distancia es el primer
personaje de esta historia: el maíz cuesta más mientras más lejos está de donde se siembra.

### Monterrey: el golpe más fuerte y el más rápido

En Guadalupe, la central que abastece a Monterrey, el maíz se compra a Tamaulipas, Sinaloa, Tabasco y
Coahuila. Ahí el choque de 2022 fue brutal. En abril el kilo costaba 10.82 pesos; en mayo, 16.25.
Fue un salto de 50 % en un solo mes, el más grande de todo el periodo. El precio se quedó por encima
de 13 pesos durante casi un año y fue el más caro de los cinco mercados todo 2022.

### Culiacán: el precio del origen

En Culiacán, en el corazón del maíz sinaloense, el choque llegó tarde y con menos fuerza. El precio
se quedó en 7 y 8 pesos durante casi todo 2022, y solo hasta finales de ese año subió a 10. Estar
junto al campo amortiguó el golpe. En 2025, en plena sequía, Culiacán fue el mercado más barato de
los cinco: 8 pesos el kilo.

### Hermosillo: el que nunca bajó

Hermosillo cuenta una historia distinta a todas. El choque le llegó poco a poco, sin un salto
grande, pero el precio nunca regresó. Pasó de 7.50 pesos en 2020 a 9 en 2022, 11.15 en 2023, 12 en
2024 y 13 en 2025. Mientras los demás mercados empezaron a bajar después de 2023, Hermosillo terminó
el periodo como el maíz más caro del país. Sonora compra parte de su maíz a Sinaloa, y la subida coincide
con la sequía de su vecino, justo cuando el resto del país se abarataba.

### Ciudad de México y Guadalajara: los mercados grandes

Iztapalapa, la central más grande del país, y Guadalajara, en el estado que más maíz blanco produce
después de Sinaloa, siguieron la trayectoria "promedio": subieron de alrededor de 6 pesos en 2020 a
un máximo de entre 11 y 13 pesos a finales de 2022 e inicios de 2023, y bajaron después a cerca de
9. Son los mercados que más se parecen a "el precio del maíz" de las noticias. Aun así, Iztapalapa
también tuvo su sacudida propia: en julio de 2023 cayó 29 % en un mes, sin que pasara nada parecido
en el resto del país.

### Lo que esto significa

Para una empresa como Gruma, que compra maíz en todo el país y en el extranjero, estas diferencias
locales se promedian y desaparecen. Eso ayuda a explicar por qué ningún mercado regional predice su
acción. Para un consumidor de Monterrey en mayo de 2022 o de Hermosillo en 2025, en cambio, el
"precio del maíz" fue mucho más alto que el promedio nacional. **[pendiente: comparar con el precio
de la tortilla en cada una de estas ciudades.]**

El choque fue mundial, pero cada región lo vivió distinto según qué tan cerca estaba del campo y de
dónde venía su grano. Hablar de un solo precio del maíz esconde a quienes lo pagaron más caro.

<div style="page-break-before: always"></div>

# Notas para decidir

| | Historia 1: ¿Quién paga? | Historia 2: La que no encontramos | Historia 3: Cinco Méxicos |
|---|---|---|---|
| Tono | Social, con tensión | Investigación, honesta | Geográfica, de contraste |
| Datos listos | Casi (falta la tortilla) | Sí, todo está en las libretas | Sí (falta la tortilla para cerrar) |
| Gráfica central | Abanico: precio al productor contra mayorista | Correlaciones y eventos de Gruma | Mapa o líneas de los 5 mercados |
| Riesgo | Insinuar abuso sin datos de márgenes | Que parezca un proyecto fallido | Que se aleje de Gruma |

**Recomendación:** usar la Historia 2 como estructura (es la pregunta original del proyecto) y la
Historia 1 como desenlace ("si la empresa no absorbe el choque, ¿quién lo hace?"). De la Historia 3
se pueden tomar Monterrey 2022 y Hermosillo 2025 como ejemplos concretos.

**Datos pendientes antes de la versión final:**

1. Precio de la tortilla por kilo (SNIIM, tortillerías por ciudad; o INPC del INEGI, genérico
   "tortilla de maíz").
2. Deflactar los precios con el INPC para hablar en términos reales.
3. Confirmar el precio mayorista de 2022–2025 mercado por mercado. La mediana nacional da justo 10
   pesos cada año, y en Culiacán el 38 % de las cotizaciones desde 2022 son exactamente 10 pesos.
4. Revisar el precio rural de Sonora y Sinaloa por ciclo (otoño-invierno contra primavera-verano).
