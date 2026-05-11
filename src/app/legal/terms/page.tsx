"use client";

import Link from "next/link";
import { ArrowLeft, Scale } from "lucide-react";

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-neutral-50">
      <div className="mx-auto max-w-3xl px-6 py-12">
        <Link
          href="/"
          className="mb-8 inline-flex items-center gap-2 text-sm text-neutral-400 transition-colors hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          Retour à l&apos;accueil
        </Link>

        <div className="mb-8 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-[#00e1ff]/10 text-[#00e1ff] ring-1 ring-white/10">
          <Scale className="h-6 w-6" />
        </div>

        <h1 className="text-3xl font-bold tracking-tight text-white">
          Conditions générales d&apos;utilisation
        </h1>
        <p className="mt-2 text-sm text-neutral-500">
          Dernière mise à jour : 10/05/2026
        </p>

        <div className="mt-10 space-y-10 text-sm leading-relaxed text-neutral-300">
          <section>
            <h2 className="text-lg font-semibold text-white">Objet du service</h2>
            <p className="mt-2">
              Synkrone est une plateforme en ligne permettant la création, la configuration et
              l&apos;hébergement de bots Discord personnalisés via des modules pré-codés. Le service
              comprend :
            </p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-neutral-400">
              <li>Un dashboard de configuration visuelle des bots</li>
              <li>Un système de modules activables/désactivables (modération, auto-rôles, économie, etc.)</li>
              <li>Un hébergement cloud optionnel des bots créés</li>
              <li>Un constructeur de sites web pour serveurs Discord</li>
              <li>Un système de monnaie virtuelle (Krônes) pour l&apos;accès aux fonctionnalités premium</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-white">Inscription et compte</h2>
            <p className="mt-2">
              L&apos;utilisation de Synkrone nécessite la création d&apos;un compte utilisateur. En
              créant un compte, vous vous engagez à :
            </p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-neutral-400">
              <li>Fournir des informations exactes, complètes et à jour</li>
              <li>Maintenir la confidentialité de vos identifiants de connexion</li>
              <li>Être âgé d&apos;au moins 13 ans (ou 16 ans dans certains pays de l&apos;UE)</li>
              <li>Ne pas créer de comptes multiples sans autorisation</li>
              <li>Notifier immédiatement Synkrone en cas d&apos;utilisation non autorisée de votre compte</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-white">Tokens Discord et sécurité</h2>
            <p className="mt-2">
              Pour fonctionner, les bots Discord nécessitent un token d&apos;authentification. En
              utilisant Synkrone :
            </p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-neutral-400">
              <li>Vous êtes seul responsable de la sécurité de vos tokens Discord</li>
              <li>Synkrone chiffre les tokens stockés sur nos serveurs</li>
              <li>En cas de fuite due à votre négligence, Synkrone ne peut être tenu responsable</li>
              <li>Vous devez révoquer immédiatement un token compromis via le Discord Developer Portal</li>
            </ul>
            <p className="mt-2 text-amber-400">
              Ne partagez jamais votre token. Celui-ci donne un contrôle total sur votre bot.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-white">Utilisation interdite</h2>
            <p className="mt-2">Il est strictement interdit d&apos;utiliser Synkrone pour :</p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-neutral-400">
              <li>Spam, harcèlement ou intimidation d&apos;utilisateurs</li>
              <li>Distribution de contenu illégal (malware, pornographie infantile, etc.)</li>
              <li>Violation des Conditions d&apos;Utilisation de Discord</li>
              <li>Attaques DDoS ou tentative de disruption de services</li>
              <li>Phishing ou usurpation d&apos;identité</li>
              <li>Exploitation de bugs ou failles de sécurité</li>
              <li>Revente non autorisée de comptes ou de services</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-white">Système de Krônes et paiements</h2>
            <p className="mt-2">
              Synkrone utilise une monnaie virtuelle appelée &quot;Krônes&quot; pour l&apos;accès aux
              fonctionnalités premium :
            </p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-neutral-400">
              <li>Les Krônes sont achetées avec de la monnaie réelle (EUR)</li>
              <li>Les Krônes n&apos;ont aucune valeur monétaire en dehors de la plateforme</li>
              <li>Aucun remboursement n&apos;est effectué sauf obligation légale</li>
              <li>Les Krônes non utilisés restent sur le compte indéfiniment</li>
              <li>Synkrone se réserve le droit de modifier les tarifs avec préavis de 30 jours</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-white">Hébergement et disponibilité</h2>
            <p className="mt-2">
              Synkrone propose un hébergement cloud optionnel pour les bots créés :
            </p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-neutral-400">
              <li>L&apos;hébergement Synkrone est fourni &quot;en l&apos;état&quot; sans garantie de disponibilité à 100%</li>
              <li>Des interruptions de service peuvent survenir pour maintenance</li>
              <li>Synkrone ne garantit pas la conservation des logs au-delà de 30 jours</li>
              <li>Les utilisateurs peuvent opter pour l&apos;auto-hébergement à tout moment</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-white">Propriété intellectuelle</h2>
            <p className="mt-2">
              Tous les éléments de Synkrone (code, design, logos, modules) sont protégés par le droit
              d&apos;auteur. L&apos;utilisation du code source fourni en cas d&apos;auto-hébergement est
              soumise à une licence limitée :
            </p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-neutral-400">
              <li>Vous ne pouvez pas revendre le code source</li>
              <li>Vous ne pouvez pas utiliser le code pour créer un service concurrent</li>
              <li>Les mises à jour sont fournies pendant la durée spécifiée à l&apos;achat</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-white">Résiliation et suspension</h2>
            <p className="mt-2">
              Synkrone se réserve le droit de suspendre ou résilier un compte en cas de :
            </p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-neutral-400">
              <li>Violation des présentes CGU</li>
              <li>Comportement nuisible envers d&apos;autres utilisateurs</li>
              <li>Tentative de compromission de la plateforme</li>
              <li>Inactivité prolongée (plus de 12 mois) pour les comptes gratuits</li>
            </ul>
            <p className="mt-2">En cas de résiliation pour violation, aucun remboursement ne sera effectué.</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-white">Contact</h2>
            <p className="mt-2">
              Pour toute question concernant ces CGU, contactez-nous à{" "}
              <a href="mailto:contact@synkrone.fr" className="text-[#00e1ff] hover:underline">
                contact@synkrone.fr
              </a>{" "}
              ou sur notre{" "}
              <a href="https://discord.gg/nuFNvVybGE" target="_blank" rel="noopener noreferrer" className="text-[#00e1ff] hover:underline">
                Discord Support
              </a>.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
