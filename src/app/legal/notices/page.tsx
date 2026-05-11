"use client";

import Link from "next/link";
import { ArrowLeft, FileText } from "lucide-react";

export default function NoticesPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-neutral-50">
      <div className="mx-auto max-w-3xl px-6 py-12">
        <Link href="/" className="mb-8 inline-flex items-center gap-2 text-sm text-neutral-400 transition-colors hover:text-white">
          <ArrowLeft className="h-4 w-4" />
          Retour à l&apos;accueil
        </Link>

        <div className="mb-8 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-[#00e1ff]/10 text-[#00e1ff] ring-1 ring-white/10">
          <FileText className="h-6 w-6" />
        </div>

        <h1 className="text-3xl font-bold tracking-tight text-white">Mentions légales</h1>
        <p className="mt-2 text-sm text-neutral-500">Mises à jour le 10/05/2026</p>

        <div className="mt-10 space-y-10 text-sm leading-relaxed text-neutral-300">
          <section>
            <h2 className="text-lg font-semibold text-white">Éditeur du site</h2>
            <p className="mt-2">Synkrone — Plateforme de création et d&apos;hébergement de bots Discord</p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-neutral-400">
              <li>Email : <a href="mailto:contact@synkrone.fr" className="text-[#00e1ff] hover:underline">contact@synkrone.fr</a></li>
              <li>Discord : <a href="https://discord.gg/nuFNvVybGE" target="_blank" rel="noopener noreferrer" className="text-[#00e1ff] hover:underline">Serveur Support</a></li>
            </ul>
            <p className="mt-2">Directeur de la publication : Noé Barneron</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-white">Hébergement</h2>
            <p className="mt-2">Hetzner Online GmbH — Industriestr. 25, 91710 Gunzenhausen, Allemagne</p>
            <p className="mt-1">OVH SAS — 2 rue Kellermann, 59100 Roubaix, France</p>
            <p className="mt-2 text-neutral-400">Les données sont hébergées principalement au sein de l&apos;Union Européenne.</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-white">Propriété intellectuelle</h2>
            <p className="mt-2">
              L&apos;ensemble du contenu du site Synkrone (textes, images, graphismes, logos, icônes, code source)
              est la propriété exclusive de Synkrone ou de ses partenaires.
            </p>
            <p className="mt-2 text-neutral-400">
              Toute reproduction, distribution, modification ou utilisation, même partielle, sans autorisation
              préalable écrite est strictement interdite et constitue une contrefaçon sanctionnée par les articles
              L.335-2 et suivants du Code de la propriété intellectuelle.
            </p>
            <p className="mt-2">
              <strong className="text-white">Marques déposées :</strong> Synkrone™, le logo Synkrone, et tous les
              noms de bots associés (Vex, Asuna, Kayaba, Yui) sont des marques déposées.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-white">Limitation de responsabilité</h2>
            <p className="mt-2">Synkrone s&apos;efforce d&apos;assurer l&apos;exactitude et la mise à jour des informations diffusées. Toutefois, Synkrone ne peut garantir l&apos;exactitude, la précision ou l&apos;exhaustivité des informations.</p>
            <p className="mt-2 text-neutral-400">Synkrone décline toute responsabilité pour :</p>
            <ul className="mt-1 list-disc space-y-1 pl-5 text-neutral-400">
              <li>toute imprécision, inexactitude ou omission des informations</li>
              <li>tous dommages résultant d&apos;une intrusion frauduleuse d&apos;un tiers</li>
              <li>les dommages indirects résultant de l&apos;utilisation du service</li>
              <li>les dysfonctionnements dus à des facteurs externes (réseau, force majeure)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-white">Cookies et collecte de données</h2>
            <p className="mt-2">
              Le site utilise des cookies essentiels au fonctionnement (session, authentification) et des cookies
              analytiques pour améliorer l&apos;expérience utilisateur. Conformément à la directive ePrivacy et au RGPD,
              les cookies non essentiels ne sont déposés qu&apos;après consentement explicite.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-white">Liens hypertextes</h2>
            <p className="mt-2">
              Le site peut contenir des liens vers d&apos;autres sites. Synkrone n&apos;exerce aucun contrôle sur ces
              sites et décline toute responsabilité quant à leur contenu. Toute création de lien vers Synkrone doit
              faire l&apos;objet d&apos;une autorisation préalable.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-white">Droit applicable et juridiction</h2>
            <p className="mt-2">
              Les présentes mentions légales sont régies par le droit français. En cas de litige, une solution amiable
              sera recherchée avant toute action judiciaire. À défaut, les tribunaux français seront compétents.
            </p>
            <p className="mt-2 text-neutral-400">
              Pour les consommateurs européens, la plateforme de règlement en ligne des litiges (RLL) de l&apos;UE est
              accessible à l&apos;adresse :{" "}
              <a href="https://ec.europa.eu/consumers/odr" target="_blank" rel="noopener noreferrer" className="text-[#00e1ff] hover:underline">ec.europa.eu/consumers/odr</a>
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-white">Contact</h2>
            <p className="mt-2">
              <a href="mailto:contact@synkrone.fr" className="text-[#00e1ff] hover:underline">contact@synkrone.fr</a>
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
